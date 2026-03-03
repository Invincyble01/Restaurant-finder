import os
import re
import json
import logging
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

import httpx
from langchain_oci import ChatOCIGenAI
from langchain.messages import AIMessage, HumanMessage
from dotenv import load_dotenv

from agent.graph.struct import AgentConfig

load_dotenv()

logger = logging.getLogger(__name__)


class ApifyPlacesAgent:
    """Direct Apify REST integration for compass/crawler-google-places.

    Maps user queries to the actor inputs per official docs and calls the
    run-sync-get-dataset-items endpoint. Returns ONLY the raw JSON array string
    of items; downstream FormatterAgent handles normalization for the UI.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self.agent_name = (config.name if config else "apify_places_agent")
        self.default_location = os.getenv("DEFAULT_LOCATION", "Austin, TX")
        self.actor_id = os.getenv("APIFY_ACTOR", "compass/crawler-google-places")
        self.base_url = os.getenv("APIFY_BASE_URL", "https://api.apify.com")
        self.token = os.getenv("APIFY_TOKEN").strip()
        self.data_mode = os.getenv("APIFY_DATA_MODE", "static").lower()
        self.static_dir = os.getenv("APIFY_STATIC_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "static_data", "apify"),)
        self.static_file = os.getenv("APIFY_STATIC_FILE", "").strip()



    async def initialize(self):
        return True

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_text = str(state["messages"][0].content)
        # Derive desired count
        count = self._extract_count(user_text, default=5)

        # Build actor input with LLM guidance; fallback to heuristic
        actor_input = await self._build_actor_input_llm(user_text, count)
        if not actor_input:
            actor_input = self._map_query_to_actor_input(user_text)
            actor_input["maxItems"] = count

        # Ensure maxItems present
        actor_input.setdefault("maxItems", count)
        actor_input.setdefault("language", "en")

        # Call Apify and return RAW items so downstream FormatterAgent
        # can normalize while preserving coordinates (lat/lng) for the map.
        items = await self._run_apify_actor(actor_input)
        items = items[:count] if isinstance(items, list) else []
        return {"messages": state["messages"] + [AIMessage(content=json.dumps(items, ensure_ascii=False))]}

    def _extract_count(self, text: str, default: int = 5) -> int:
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
            t = re.sub(rf"(?i)\b(?:in|near|around|at)\s+{loc_re}(?:\b|$)", "", t).strip()
        # Remove any generic trailing location phrase if it remains
        t = re.sub(r"(?i)\b(?:in|near|around|at)\s+[A-Za-z][^,;:.!?]*$", "", t).strip()
        # Collapse whitespace and stray punctuation
        t = re.sub(r"\s{2,}", " ", t).strip(" ,.-")
        # Ensure a place-type keyword exists (kept from previous behavior)
        if not re.search(r"(?i)\b(restaurant|restaurants|cafe|cafes|coffee|bar|bistro)\b", t):
            t = f"{t} restaurants" if t else "restaurants"
        return t

    def _ensure_search_string(self, text: str) -> str:
        t = text.strip()
        # Remove prefix like "Top 5" etc.
        t = re.sub(r"(?i)\btop\s+\d+\b", "", t).strip()
        # Ensure a place-type keyword exists
        if not re.search(r"(?i)\b(restaurant|restaurants|cafe|cafes|coffee|bar|bistro)\b", t):
            t = f"{t} restaurants"
        # Ensure location
        # If user already provided a probable location word (e.g., Hyderabad), don't append default
        has_in_phrase = re.search(r"(?i)\bin\s+.+", t)
        has_comma_place = ("," in t)
        probable_city_word = re.search(r"(?<!\S)[A-Z][a-zA-Z]+(\s+[A-Z][a-zA-Z]+)*", t)
        if not (has_in_phrase or has_comma_place or probable_city_word):
            t = f"{t} in {self.default_location}"
        return t

    def _map_query_to_actor_input(self, user_text: str) -> Dict[str, Any]:
        count = self._extract_count(user_text, default=5)
        maps_url = self._extract_url(user_text)

        actor_input: Dict[str, Any] = {"maxItems": count, "language": "en"}

        if maps_url:
            actor_input["startUrls"] = [{"url": maps_url}]
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

    async def _build_actor_input_llm(self, user_text: str, count: int) -> Optional[Dict[str, Any]]:
        """Use LLM to craft valid actor input JSON.
        - Prefer searchStringsArray with 1–3 optimized queries
        - If a Google Maps URL is present, use startUrls instead
        - Always include maxItems and language: 'en'
        - If user provided a location (e.g., Hyderabad), DO NOT append default location
        """
        guidelines = (
            "Build input for Apify actor 'compass/crawler-google-places'. Return JSON only.\n"
            "Include: maxItems (int), language ('en'), and one of: searchStringsArray (preferred), startUrls, or categoryFilterWords.\n"
            "Use locationQuery for the location. Do NOT include the location inside searchStringsArray.\n"
            f"If the user did not provide a location, set locationQuery to '{self.default_location}'.\n"
            "If a Google Maps URL is present, use startUrls instead of searchStringsArray.\n"
            "Provide 1-3 search strings; (e.g., 'chinese restaurants', 'coffee shops')."
        )
        prompt = (
            f"USER_QUERY: {user_text}\n"
            f"DEFAULT_LOCATION: {self.default_location}\n"
            f"COUNT: {count}\n"
            "Return JSON only."
        )
        try:
            resp = await self._oci_llm(0.2).ainvoke([HumanMessage(content=guidelines + "\n\n" + prompt)])
            text = str(resp.content).strip().strip("` ")
            if text.lower().startswith("json"):
                text = text[4:].strip()
            data = json.loads(text)
            if not isinstance(data, dict):
                return None
            out: Dict[str, Any] = {"maxItems": max(1, min(50, int(count))), "language": "en"}
            if data.get("startUrls"):
                out["startUrls"] = data["startUrls"]
            if data.get("categoryFilterWords"):
                out["categoryFilterWords"] = data["categoryFilterWords"][:5]
            if isinstance(data.get("maxItems"), int):
                out["maxItems"] = max(1, min(50, int(data["maxItems"])) )
            if isinstance(data.get("language"), str):
                out["language"] = data["language"]
            # If startUrls not present, enforce/synthesize locationQuery and sanitize search strings
            if not out.get("startUrls"):
                loc = data.get("locationQuery")
                if isinstance(loc, str) and loc.strip():
                    out["locationQuery"] = loc.strip()
                else:
                    out["locationQuery"] = self.default_location
                if data.get("searchStringsArray"):
                    terms: List[str] = []
                    for t in data["searchStringsArray"][:3]:
                        if isinstance(t, str):
                            cleaned = self._sanitize_query_terms(t, out["locationQuery"]) \
                                if hasattr(self, "_sanitize_query_terms") else t
                            if cleaned:
                                terms.append(cleaned)
                    if terms:
                        out["searchStringsArray"] = terms
            # Ensure at least one required key besides maxItems/language
            if not any(k in out for k in ("searchStringsArray", "startUrls", "categoryFilterWords")):
                return None
            return out
        except Exception as e:
            logger.warning("LLM actor-input mapping failed; using heuristic. Error: %s", e)
            return None

    async def _summarize_places_llm(self, items: List[Dict[str, Any]], count: int) -> Optional[List[Dict[str, Any]]]:
        if not items:
            return []
        schema_hint = (
            "Return a JSON array of exactly N items with keys: name, caption, rating, location, imageURL, infoLink.\n"
            "- name ← 'title' (or 'name')\n"
            "- caption ← 'categoryName' or first of 'categories'\n"
            "- rating ← unicode stars from numeric 'totalScore' (>=4.5★★★★★, >=3.5★★★★☆, >=2.5★★★☆☆, >=1.5★★☆☆☆, >=0.5★☆☆☆☆, else ☆☆☆☆☆)\n"
            "- location ← 'address' (or 'city' + 'state')\n"
            "- imageURL ← 'imageUrl' if present\n"
            "- infoLink ← 'website' else 'url' else 'searchPageUrl'\n"
        )
        prompt = (
            f"N={count}. {schema_hint} Return JSON only. RAW_ITEMS: {json.dumps(items)[:120000]}"
        )
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

    def _fallback_projection(self, items: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
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
            caption = it.get("categoryName") or (it.get("categories") or [None])[0] or "Popular spot"
            rating_s = stars(it.get("totalScore") or it.get("rating"))
            location = it.get("address") or ", ".join([v for v in [it.get("city"), it.get("state")] if v]) or self.default_location
            image = it.get("imageUrl") or ""
            info = it.get("website") or it.get("url") or it.get("searchPageUrl") or ""
            out.append({
                "name": name,
                "caption": caption,
                "rating": rating_s,
                "location": location,
                "imageURL": image,
                "infoLink": info,
            })
        i = 0
        while len(out) < count and out:
            out.append(out[i])
            i += 1
        return out

    async def _run_apify_actor(self, actor_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        if self.data_mode == "static" or (not self.token or self.token.startswith("<")):
            return self._load_static_items(actor_input)

        url = f"{self.base_url}/v2/acts/{self.actor_id.replace('/', '~')}/run-sync-get-dataset-items"
        headers = {"Authorization": f"Bearer {self.token}", "X-Apify-Token": self.token}
        logger.info("Running Apify actor '%s' with input: %s", self.actor_id, json.dumps(actor_input))

        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(url, json=actor_input, headers=headers)
                if resp.status_code >= 400:
                    logger.error(
                        "Apify REST call failed: %s %s — %s",
                        resp.status_code,
                        resp.reason_phrase,
                        resp.text[:500],
                    )
                    return []
                data = resp.json()
                if isinstance(data, dict) and "items" in data:
                    return data.get("items", [])
                if isinstance(data, list):
                    return data
                return []
            except httpx.RequestError as e:
                logger.exception("Apify REST network error: %s", e)
                return []
            except Exception as e:
                logger.exception("Apify REST unexpected error: %s", e)
                return []

    def _load_static_items(self, actor_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Load Apify-shaped JSON items from local fixtures.
        Selection order:
        1) APIFY_STATIC_FILE if provided
        2) Heuristic based on searchStringsArray[0] and locationQuery
        3) default.json
        """
        # 1) explicit override via APIFY_STATIC_FILE
        if getattr(self, "static_file", ""):
            path = os.path.join(getattr(self, "static_dir", os.getcwd()), self.static_file)
            return self._read_json_list(path)

        # 2) heuristic
        query = "".join(actor_input.get("searchStringsArray", [])[:1]).lower()
        location = str(actor_input.get("locationQuery", "")).lower().replace(",", "").strip()

        def slug(*parts: str) -> str:
            return "_".join([str(p).strip().replace(" ", "-") for p in parts if p]).lower() + ".json"

        candidates: List[str] = []
        if "chinese" in query and ("austin" in query or "austin" in location):
            candidates.append(slug("chinese", "in", "austin"))
        if "italian" in query and ("hyderabad" in query or "hyderabad" in location):
            candidates.append(slug("italian", "in", "hyderabad"))
        if "continental" in query and ("london" in query or "london" in location):
            candidates.append(slug("continental", "in", "london"))
        if "indian" in query and ("new york" in query or "new-york" in location or "nyc" in location):
            candidates.append("7_indian_in_new-york.json")
        if ("cafe" in query or "cafes" in query) and ("france" in query or "france" in location):
            candidates.append(slug("cafes", "in", "france"))

        if not candidates and query:
            first = query.split()[0]
            if location:
                candidates.append(slug(first, "in", location))

        for name in candidates:
            path = os.path.join(getattr(self, "static_dir", os.getcwd()), name)
            if os.path.exists(path):
                return self._read_json_list(path)

        # 3) fallback to default.json
        default_path = os.path.join(getattr(self, "static_dir", os.getcwd()), "default.json")
        if os.path.exists(default_path):
            return self._read_json_list(default_path)

        logger.warning("No matching static Apify fixture found. Returning empty list.")
        return []


    def _read_json_list(self, path: str) -> List[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error("Failed reading static data file %s: %s", path, e)
            return []
        if isinstance(data, dict) and "items" in data:
            return data.get("items", [])
        if isinstance(data, list):
            return data
        return []
