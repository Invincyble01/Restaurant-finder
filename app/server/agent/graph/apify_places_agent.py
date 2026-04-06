import os
import re
import json
import random
import logging
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

from langchain_oci import ChatOCIGenAI
from langchain.messages import AIMessage, HumanMessage
from dotenv import load_dotenv

from agent.graph.struct import AgentConfig
from agent.graph.places_providers import (
    PlacesProvider,
    create_places_provider,
    resolve_places_provider_mode,
)

load_dotenv()

logger = logging.getLogger(__name__)


class ApifyPlacesAgent:
    """Fetch raw restaurant data while preserving the formatter contract."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.agent_name = config.name if config else "apify_places_agent"
        self.default_location = os.getenv("DEFAULT_LOCATION", "Austin, TX")
        self.actor_id = os.getenv("APIFY_ACTOR", "compass/crawler-google-places")
        self.provider_mode = resolve_places_provider_mode()
        self.provider: PlacesProvider = create_places_provider(
            actor_id=self.actor_id,
            default_location=self.default_location,
        )

    async def initialize(self):
        await self.provider.initialize()
        return True

    async def close(self):
        await self.provider.close()

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_text = str(state["messages"][0].content)
        # Derive desired count
        count = self._extract_count(user_text, default=10)

        # Build actor input with LLM guidance; fallback to heuristic
        actor_input = await self._build_actor_input_llm(user_text, count)
        if not actor_input:
            actor_input = self._map_query_to_actor_input(user_text)

        actor_input = self._sanitize_actor_input(
            actor_input, count
        ) or self._map_query_to_actor_input(user_text)

        # Call Apify and return RAW items so downstream FormatterAgent
        # can normalize while preserving coordinates (lat/lng) for the map.
        items = await self.provider.fetch_items(actor_input)
        logger.info(
            "ApifyPlacesAgent provider '%s' returned %s raw items before sampling.",
            self.provider_mode,
            len(items) if isinstance(items, list) else 0,
        )
        items = self._sample_items(items, count)
        logger.info(
            "ApifyPlacesAgent provider '%s' returned %s items after sampling.",
            self.provider_mode,
            len(items),
        )
        return {
            "messages": state["messages"]
            + [AIMessage(content=json.dumps(items, ensure_ascii=False))]
        }

    @staticmethod
    def _sample_items(items: Any, count: int) -> List[Dict[str, Any]]:
        if not isinstance(items, list):
            return []
        dict_items = [item for item in items if isinstance(item, dict)]
        if not dict_items:
            return []
        sample_size = min(max(1, count), len(dict_items))
        return random.sample(dict_items, sample_size)

    def _extract_count(self, text: str, default: int = 10) -> int:
        m = re.search(r"(\d+)", text)
        try:
            return max(1, min(50, int(m.group(1)))) if m else default
        except Exception:
            return default

    def _extract_url(self, text: str) -> Optional[str]:
        for tok in text.split():
            if tok.startswith("http://") or tok.startswith("https://"):
                try:
                    p = urlparse(tok)
                    if p.scheme in ("http", "https") and p.netloc:
                        return tok
                except Exception:
                    pass
        return None

    def _extract_place_ids(self, text: str) -> List[str]:
        if not text:
            return []
        matches = re.findall(r"\bChI[A-Za-z0-9_-]{8,}\b", text)
        out: List[str] = []
        for pid in matches:
            if pid not in out:
                out.append(pid)
        return out

    def _extract_location(self, text: str) -> Optional[str]:
        t = (text or "").strip()
        if not t:
            return None
        # Trailing comma pattern: "..., Tokyo"
        m = re.search(r",\s*([^,;:.!?]+)\s*$", t)
        if m:
            cand = m.group(1).strip()
        else:
            # Prepositions near end: in/near/around/at <place>
            m = re.search(r"(?i)\b(?:in|near|around|at)\s+([A-Za-z][^,;:.!?]+)\s*$", t)
            cand = m.group(1).strip() if m else None
        if cand:
            cand = re.sub(r"\s+", " ", cand)
            if re.search(r"[A-Za-z]", cand):
                return cand
        return None

    def _sanitize_query_terms(self, text: str, location: Optional[str]) -> str:
        t = (text or "").strip()
        # Remove prefixes like "Top 5"
        t = re.sub(r"(?i)\btop\s+\d+\b", "", t).strip()
        if location:
            loc_re = re.escape(location.strip())
            # Remove trailing ", <location>"
            t = re.sub(rf",\s*{loc_re}\s*$", "", t, flags=re.IGNORECASE)
            # Remove " in/near/around/at <location>" regardless of case
            t = re.sub(
                rf"(?i)\b(?:in|near|around|at)\s+{loc_re}(?:\b|$)", "", t
            ).strip()
        # Remove any generic trailing location phrase if it remains
        t = re.sub(r"(?i)\b(?:in|near|around|at)\s+[A-Za-z][^,;:.!?]*$", "", t).strip()
        # Collapse whitespace and stray punctuation
        t = re.sub(r"\s{2,}", " ", t).strip(" ,.-")
        # Ensure a place-type keyword exists (kept from previous behavior)
        if not re.search(
            r"(?i)\b(restaurant|restaurants|cafe|cafes|coffee|bar|bistro)\b", t
        ):
            t = f"{t} restaurants" if t else "restaurants"
        return t

    def _normalize_start_urls(self, value: Any) -> List[Dict[str, str]]:
        entries = value if isinstance(value, list) else [value]
        start_urls: List[Dict[str, str]] = []
        for entry in entries:
            url = None
            if isinstance(entry, dict):
                url = entry.get("url")
            elif isinstance(entry, str):
                url = entry
            if not isinstance(url, str):
                continue
            candidate = url.strip()
            if not candidate:
                continue
            try:
                parsed = urlparse(candidate)
            except Exception:
                continue
            if parsed.scheme in ("http", "https") and parsed.netloc:
                start_urls.append({"url": candidate})
            if len(start_urls) >= 10:
                break
        return start_urls

    def _normalize_place_ids(self, value: Any) -> List[str]:
        if isinstance(value, str):
            parts = re.split(r"[\s,]+", value.strip())
        elif isinstance(value, list):
            parts = [str(v).strip() for v in value if isinstance(v, str)]
        else:
            return []

        out: List[str] = []
        for part in parts:
            if re.fullmatch(r"ChI[A-Za-z0-9_-]{8,}", part) and part not in out:
                out.append(part)
            if len(out) >= 25:
                break
        return out

    def _normalize_search_strings(
        self, value: Any, location: Optional[str]
    ) -> List[str]:
        if isinstance(value, str):
            raw_terms: List[str] = [value]
        elif isinstance(value, list):
            raw_terms = [t for t in value if isinstance(t, str)]
        else:
            raw_terms = []

        out: List[str] = []
        for term in raw_terms[:5]:
            cleaned = self._sanitize_query_terms(term, location)
            if cleaned and cleaned not in out:
                out.append(cleaned)
            if len(out) >= 3:
                break
        return out

    @staticmethod
    def _to_bool(value: Any) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        return None

    def _sanitize_actor_input(
        self, candidate: Dict[str, Any], count: int
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(candidate, dict):
            return None

        safe_count = self._extract_count(
            str(candidate.get("maxCrawledPlacesPerSearch", count)), default=count
        )
        if "maxCrawledPlacesPerSearch" in candidate:
            try:
                safe_count = max(
                    1, min(50, int(candidate["maxCrawledPlacesPerSearch"]))
                )
            except Exception:
                safe_count = count
        elif "maxItems" in candidate:
            try:
                safe_count = max(1, min(50, int(candidate["maxItems"])))
            except Exception:
                safe_count = count

        out: Dict[str, Any] = {
            "maxCrawledPlacesPerSearch": max(1, min(50, safe_count)),
            "language": "en",
            "searchMatching": "all",
            "skipClosedPlaces": True,
            "includeWebResults": False,
        }

        language = candidate.get("language")
        if isinstance(language, str) and language.strip():
            out["language"] = language.strip()

        search_matching = candidate.get("searchMatching")
        if search_matching in ("all", "any"):
            out["searchMatching"] = search_matching

        skip_closed = self._to_bool(candidate.get("skipClosedPlaces"))
        if skip_closed is not None:
            out["skipClosedPlaces"] = skip_closed

        include_web = self._to_bool(candidate.get("includeWebResults"))
        if include_web is not None:
            out["includeWebResults"] = include_web

        start_urls = self._normalize_start_urls(candidate.get("startUrls"))
        place_ids = self._normalize_place_ids(candidate.get("placeIds"))

        location = candidate.get("locationQuery")
        if not isinstance(location, str) or not location.strip():
            location = self.default_location
        location = location.strip()

        search_strings = self._normalize_search_strings(
            candidate.get("searchStringsArray"), location
        )

        if start_urls:
            out["startUrls"] = start_urls
        elif place_ids:
            out["placeIds"] = place_ids
        else:
            out["locationQuery"] = location
            if search_strings:
                out["searchStringsArray"] = search_strings
            else:
                return None

        return out

    def _map_query_to_actor_input(self, user_text: str) -> Dict[str, Any]:
        count = self._extract_count(user_text, default=10)
        maps_url = self._extract_url(user_text)
        place_ids = self._extract_place_ids(user_text)
        actor_input: Dict[str, Any] = {
            "maxCrawledPlacesPerSearch": count,
            "language": "en",
            "searchMatching": "all",
            "skipClosedPlaces": True,
            "includeWebResults": False,
        }

        if maps_url:
            actor_input["startUrls"] = [{"url": maps_url}]
        elif place_ids:
            actor_input["placeIds"] = place_ids
        else:
            loc = self._extract_location(user_text) or self.default_location
            terms = self._sanitize_query_terms(user_text, loc)
            actor_input["locationQuery"] = loc
            actor_input["searchStringsArray"] = [terms]

        return actor_input

    def _oci_llm(self, temperature: float = 0.2) -> ChatOCIGenAI:
        return ChatOCIGenAI(
            model_id="openai.gpt-4.1",
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs={"temperature": temperature},
            auth_profile=os.getenv("AUTH_PROFILE"),
        )

    async def _build_actor_input_llm(
        self, user_text: str, count: int
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to craft valid actor input JSON.
        - Prefer searchStringsArray with 1–3 optimized queries
        - If a Google Maps URL is present, use startUrls instead
        - Support placeIds when present
        - Always include maxCrawledPlacesPerSearch and language: 'en'
        - If user provided a location, keep it in locationQuery only
        """
        guidelines = (
            "Build input for Apify actor 'compass/crawler-google-places'. Return JSON only.\n"
            "Use ONLY actor-supported keys: maxCrawledPlacesPerSearch, language, searchMatching, skipClosedPlaces, includeWebResults, searchStringsArray, locationQuery, startUrls, placeIds.\n"
            "Include one source among: searchStringsArray (+ locationQuery), startUrls, or placeIds.\n"
            "Use locationQuery for the location. Do NOT include the location inside searchStringsArray.\n"
            f"If the user did not provide a location, set locationQuery to '{self.default_location}'.\n"
            "If a Google Maps URL is present, use startUrls instead of searchStringsArray.\n"
            "If place IDs are present, use placeIds.\n"
            f"Set maxCrawledPlacesPerSearch to {count}. Use language 'en', searchMatching 'all', skipClosedPlaces true, includeWebResults false unless user asks otherwise.\n"
            "Provide 1-3 search strings (e.g., 'chinese restaurants', 'coffee shops')."
        )
        prompt = (
            f"USER_QUERY: {user_text}\n"
            f"DEFAULT_LOCATION: {self.default_location}\n"
            f"COUNT: {count}\n"
            "Return JSON only."
        )
        try:
            resp = await self._oci_llm(0.2).ainvoke(
                [HumanMessage(content=guidelines + "\n\n" + prompt)]
            )
            text = str(resp.content).strip().strip("` ")
            if text.lower().startswith("json"):
                text = text[4:].strip()
            data = json.loads(text)
            if not isinstance(data, dict):
                return None
            return self._sanitize_actor_input(data, count)
        except Exception as e:
            logger.warning(
                "LLM actor-input mapping failed; using heuristic. Error: %s", e
            )
            return None

    async def _summarize_places_llm(
        self, items: List[Dict[str, Any]], count: int
    ) -> Optional[List[Dict[str, Any]]]:
        if not items:
            return []
        schema_hint = (
            "Return a JSON array of exactly N items with keys: name, detail, rating, address, imageUrl, infoLink.\n"
            "- name ← 'title' (or 'name')\n"
            "- detail ← 'categoryName' or first of 'categories' or description\n"
            "- rating ← unicode stars from numeric 'totalScore' (>=4.5★★★★★, >=3.5★★★★☆, >=2.5★★★☆☆, >=1.5★★☆☆☆, >=0.5★☆☆☆☆, else ☆☆☆☆☆)\n"
            "- address ← 'address' (or 'city' + 'state')\n"
            "- imageUrl ← 'imageUrl' if present\n"
            "- infoLink ← 'website' else 'url' else 'searchPageUrl'\n"
        )
        prompt = f"N={count}. {schema_hint} Return JSON only. RAW_ITEMS: {json.dumps(items)[:120000]}"
        try:
            resp = await self._oci_llm(0.2).ainvoke([HumanMessage(content=prompt)])
            text = str(resp.content).strip().strip("` ")
            if text.lower().startswith("json"):
                text = text[4:].strip()
            data = json.loads(text)
            if isinstance(data, list):
                if len(data) > count:
                    data = data[:count]
                elif len(data) < count and data:
                    i = 0
                    while len(data) < count and i < len(data):
                        data.append(data[i])
                        i += 1
                return data
            return None
        except Exception as e:
            logger.warning("LLM summarization failed; using fallback. Error: %s", e)
            return None

    def _fallback_projection(
        self, items: List[Dict[str, Any]], count: int
    ) -> List[Dict[str, Any]]:
        def stars(val: Optional[float]) -> str:
            try:
                r = float(val)
            except Exception:
                return "★★★★☆"
            if r >= 4.5:
                return "★★★★★"
            if r >= 3.5:
                return "★★★★☆"
            if r >= 2.5:
                return "★★★☆☆"
            if r >= 1.5:
                return "★★☆☆☆"
            if r >= 0.5:
                return "★☆☆☆☆"
            return "☆☆☆☆☆"

        out: List[Dict[str, Any]] = []
        for it in items[:count]:
            name = it.get("title") or it.get("name") or "Unknown"
            detail = (
                it.get("categoryName")
                or (it.get("categories") or [None])[0]
                or it.get("description")
                or "Popular spot"
            )
            rating_s = stars(it.get("totalScore") or it.get("rating"))
            address = (
                it.get("address")
                or ", ".join([v for v in [it.get("city"), it.get("state")] if v])
                or self.default_location
            )
            image = it.get("imageUrl") or ""
            info = it.get("website") or it.get("url") or it.get("searchPageUrl") or ""
            out.append(
                {
                    "name": name,
                    "detail": detail,
                    "rating": rating_s,
                    "address": address,
                    "imageUrl": image,
                    "infoLink": info,
                }
            )
        i = 0
        while len(out) < count and out:
            out.append(out[i])
            i += 1
        return out
