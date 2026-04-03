import json
import os
import re
import random
from urllib.parse import quote_plus
from typing import Any, Dict, List, Optional, Tuple

from langchain.agents import create_agent
from langchain_oci import ChatOCIGenAI
from langchain.messages import HumanMessage, AIMessage


FORMATTER_PROMPT = (
    "You normalize restaurant and cafe search results into a strict JSON array.\n"
    "Input: a JSON array of place objects from a web scraper (fields may vary).\n"
    "Output: ONLY a JSON array (no prose) where each element has exactly these keys: \n"
    "- name (string)\n"
    "- detail (string: short descriptor like cuisine or categories)\n"
    "- rating (string in the form '4.8' or '4.8 | 3456 ratings')\n"
    "- address (string: formatted address or city)\n"
    "- imageUrl (string: absolute URL to an image)\n"
    "- tags (string, optional: short highlights joined by ' | ')\n"
    "- lat (number, optional)\n"
    "- lng (number, optional)\n"
    "- infoLink (string: https URL for more info)\n"
    "- infoLinkMarkdown (string, optional: markdown link labeled exactly 'Visit site')\n\n"
    "Rules:\n"
    "- If a numeric rating 0-5 exists, preserve it as a number string (for example '4.8'). Append ' | N ratings' when reviewsCount exists.\n"
    "- Apify field precedence: title over name, categoryName over categories over description, totalScore over rating, address over city/state, imageUrl over imageURL, website over url over searchPageUrl.\n"
    "- detail: join up to 3 values from categories when categoryName is missing.\n"
    "- infoLink: prefer website/url/searchPageUrl/link; otherwise create a Google Maps search link using the name and address.\n"
    "- infoLinkMarkdown: format as [Visit site](https://example.com) from infoLink.\n"
    "- imageUrl: prefer imageUrl/imageURL/photo.url/thumbnail/image/photoUrl if present; if none, leave an empty string. Do not invent images.\n"
    "- address: prefer address/formattedAddress/fullAddress/vicinity/location(string); else city/state; else default city.\n"
    "- lat/lng: if available in raw data as location/latitude/longitude/coords/geo, include numeric values (WGS84). If missing, omit keys.\n"
    "- tags: derive up to 3 concise highlights from additionalInfo when available (example: 'Vegetarian options | Bar onsite | Free street parking').\n"
    "- Never include commentary, only the JSON array.\n"
)


class FormatterAgent:
    """LLM-based formatter that ensures fields required by the UI are present."""

    def __init__(self, default_city: str | None = None):
        self.default_city = default_city or os.getenv("DEFAULT_LOCATION", "Austin, TX")
        self._agent = self._build_agent()

    def _build_agent(self):
        client = ChatOCIGenAI(
            model_id="openai.gpt-4.1",
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs={"temperature": 0.2},
            auth_profile=os.getenv("AUTH_PROFILE"),
        )

        return create_agent(
            model=client,
            tools=[],
            system_prompt=FORMATTER_PROMPT,
            name="formatter_agent",
        )

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        cleaned = (text or "").strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    @staticmethod
    def _extract_items(payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            nested = payload.get("items")
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return []

    @staticmethod
    def _as_non_empty_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text if text else None
        text = str(value).strip()
        return text if text else None

    @classmethod
    def _first_non_empty(cls, *values: Any) -> Optional[str]:
        for value in values:
            text = cls._as_non_empty_string(value)
            if text:
                return text
        return None

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            parsed = float(value)
            return parsed
        except Exception:
            return None

    @staticmethod
    def _nested_get(item: Dict[str, Any], dotted_path: str) -> Any:
        cur: Any = item
        for part in dotted_path.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part)
        return cur

    def _extract_coords(self, item: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        coord_candidates = []
        location = item.get("location")
        if isinstance(location, dict):
            coord_candidates.append(location)
        coord_candidates.append({"lat": item.get("lat"), "lng": item.get("lng")})
        coord_candidates.append(
            {"lat": item.get("latitude"), "lng": item.get("longitude")}
        )

        for key in ("coords", "geo"):
            val = item.get(key)
            if isinstance(val, dict):
                coord_candidates.append(val)

        geometry = item.get("geometry")
        if isinstance(geometry, dict):
            geom_loc = geometry.get("location")
            if isinstance(geom_loc, dict):
                coord_candidates.append(geom_loc)

        for candidate in coord_candidates:
            lat = self._to_float(
                candidate.get("lat") if isinstance(candidate, dict) else None
            )
            if lat is None and isinstance(candidate, dict):
                lat = self._to_float(candidate.get("latitude"))

            lng = self._to_float(
                candidate.get("lng") if isinstance(candidate, dict) else None
            )
            if lng is None and isinstance(candidate, dict):
                lng = self._to_float(candidate.get("lon"))
            if lng is None and isinstance(candidate, dict):
                lng = self._to_float(candidate.get("longitude"))

            if lat is not None and lng is not None:
                return lat, lng
        return None

    @classmethod
    def _normalize_score_text(cls, value: Any) -> Optional[str]:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return str(value)

        text = cls._as_non_empty_string(value)
        if not text:
            return None

        numeric_match = re.search(r"\d+(?:\.\d+)?", text)
        return numeric_match.group(0) if numeric_match else None

    @staticmethod
    def _normalize_reviews_count(item: Dict[str, Any]) -> Optional[int]:
        raw_reviews = item.get("reviewsCount")
        if raw_reviews is None or isinstance(raw_reviews, bool):
            return None
        if isinstance(raw_reviews, (int, float)):
            return int(raw_reviews) if raw_reviews >= 0 else None
        if isinstance(raw_reviews, str):
            digits = re.sub(r"[^\d]", "", raw_reviews)
            if digits:
                try:
                    parsed = int(digits)
                    return parsed if parsed >= 0 else None
                except Exception:
                    return None
        return None

    def _normalize_rating(self, item: Dict[str, Any]) -> str:
        rating_val = item.get("rating")
        score_text = self._normalize_score_text(item.get("totalScore"))
        if score_text is None:
            score_text = self._normalize_score_text(rating_val)

        if score_text is None:
            rating_text = self._as_non_empty_string(rating_val)
            if rating_text and any(ch in rating_text for ch in ("★", "☆")):
                full_stars = min(len(re.findall(r"★", rating_text)), 5)
                score_text = f"{float(full_stars):.1f}"

        reviews = self._normalize_reviews_count(item)
        if score_text:
            return (
                f"{score_text} | {reviews} ratings"
                if reviews is not None
                else score_text
            )
        return f"{reviews} ratings" if reviews is not None else ""

    def _normalize_detail(self, item: Dict[str, Any]) -> str:
        category_name = self._as_non_empty_string(item.get("categoryName"))
        if category_name:
            return category_name

        categories = item.get("categories")
        if isinstance(categories, list):
            names = []
            for entry in categories:
                text = self._as_non_empty_string(entry)
                if text:
                    names.append(text)
                if len(names) == 3:
                    break
            if names:
                return ", ".join(names)

        return (
            self._first_non_empty(
                item.get("description"),
                item.get("caption"),
                item.get("detail"),
                "Popular spot",
            )
            or "Popular spot"
        )

    def _normalize_address(self, item: Dict[str, Any]) -> str:
        location_value = item.get("location")
        location_string = location_value if isinstance(location_value, str) else None
        city = self._as_non_empty_string(item.get("city"))
        state = self._as_non_empty_string(item.get("state"))
        city_state = ", ".join([part for part in (city, state) if part])

        return (
            self._first_non_empty(
                item.get("address"),
                item.get("formattedAddress"),
                item.get("fullAddress"),
                item.get("vicinity"),
                location_string,
                city_state,
                self.default_city,
            )
            or self.default_city
        )

    def _normalize_image_url(self, item: Dict[str, Any]) -> str:
        image_obj = item.get("image")
        image_obj_url = None
        if isinstance(image_obj, dict):
            image_obj_url = self._first_non_empty(
                image_obj.get("url"), image_obj.get("src")
            )
        elif isinstance(image_obj, str):
            image_obj_url = image_obj

        return (
            self._first_non_empty(
                item.get("imageUrl"),
                item.get("imageURL"),
                self._nested_get(item, "photo.url"),
                item.get("thumbnail"),
                image_obj_url,
                item.get("photoUrl"),
                "",
            )
            or ""
        )

    def _normalize_info_link(
        self, item: Dict[str, Any], name: str, address: str
    ) -> str:
        raw_link = self._first_non_empty(
            item.get("website"),
            item.get("url"),
            item.get("searchPageUrl"),
            item.get("infoLink"),
            item.get("link"),
        )
        if raw_link:
            # Support markdown-style links from legacy fixtures.
            markdown_match = re.match(r"^\[[^\]]+\]\((https?://[^)]+)\)$", raw_link)
            if markdown_match:
                return markdown_match.group(1)
            return raw_link
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(f'{name} {address}')}"

    @staticmethod
    def _normalize_info_link_markdown(link: str) -> str:
        safe_link = (link or "").strip()
        if not safe_link:
            return ""
        return f"[Visit site]({safe_link})"

    def _normalize_tags(self, item: Dict[str, Any]) -> str:
        additional_info = item.get("additionalInfo")
        if not isinstance(additional_info, dict):
            return ""

        def collect_true_labels(entries: Any) -> List[str]:
            if not isinstance(entries, list):
                return []

            labels: List[str] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                for label, is_enabled in entry.items():
                    if is_enabled is True and isinstance(label, str) and label.strip():
                        labels.append(label.strip())
            return labels

        candidates: List[str] = []
        seen: set[str] = set()
        for category_entries in additional_info.values():
            for label in collect_true_labels(category_entries):
                key = label.casefold()
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(label)

        if not candidates:
            return ""

        selected = random.sample(candidates, min(3, len(candidates)))
        return " | ".join(selected)

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        name = (
            self._first_non_empty(item.get("title"), item.get("name"), "Unknown")
            or "Unknown"
        )
        detail = self._normalize_detail(item)
        address = self._normalize_address(item)
        info_link = self._normalize_info_link(item, name, address)
        normalized = {
            "name": name,
            "detail": detail,
            "rating": self._normalize_rating(item),
            "address": address,
            "imageUrl": self._normalize_image_url(item),
            "infoLink": info_link,
            "infoLinkMarkdown": self._normalize_info_link_markdown(info_link),
            "tags": self._normalize_tags(item),
        }

        coords = self._extract_coords(item)
        if coords:
            normalized["lat"], normalized["lng"] = coords
        return normalized

    def _extract_llm_content(self, result: Any) -> str:
        if isinstance(result, dict):
            messages = result.get("messages")
            if isinstance(messages, list) and messages:
                last_msg = messages[-1]
                content = getattr(last_msg, "content", None)
                if content is None and isinstance(last_msg, dict):
                    content = last_msg.get("content")
            else:
                content = result.get("content")
        else:
            content = getattr(result, "content", None)

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str):
                        text_parts.append(text)
            return "\n".join(text_parts)
        return ""

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw JSON list and returns canonicalized restaurant items for the UI.
        Apify raw field names are treated as highest-precedence source fields.
        """
        raw = str(state["messages"][-1].content)
        raw_for_llm = raw
        source_items: List[Dict[str, Any]] = []

        try:
            parsed_payload = json.loads(raw)
            source_items = self._extract_items(parsed_payload)
            raw_for_llm = json.dumps(parsed_payload, ensure_ascii=False)
        except Exception:
            source_items = []

        prompt = (
            f"DEFAULT_CITY: {self.default_city}\n"
            f"RAW_ITEMS_JSON: {raw_for_llm}\n"
            "Return ONLY the normalized JSON array as described."
        )
        llm_items: List[Dict[str, Any]] = []
        try:
            result = await self._agent.ainvoke(
                {"messages": [HumanMessage(content=prompt)]}
            )
            llm_content = self._extract_llm_content(result)
            cleaned = self._strip_code_fences(llm_content)
            llm_payload = json.loads(cleaned)
            llm_items = self._extract_items(llm_payload)
        except Exception:
            llm_items = []

        chosen_items = llm_items or source_items
        if llm_items and source_items:
            merged_items: List[Dict[str, Any]] = []
            for idx, item in enumerate(llm_items):
                merged = {}
                if idx < len(source_items) and isinstance(source_items[idx], dict):
                    merged.update(source_items[idx])
                if isinstance(item, dict):
                    merged.update(item)
                merged_items.append(merged if merged else item)
            if len(source_items) > len(llm_items):
                merged_items.extend(source_items[len(llm_items) :])
            chosen_items = merged_items
        normalized_items = [self._normalize_item(item) for item in chosen_items]

        return {
            "messages": state["messages"]
            + [AIMessage(content=json.dumps(normalized_items, ensure_ascii=False))]
        }
