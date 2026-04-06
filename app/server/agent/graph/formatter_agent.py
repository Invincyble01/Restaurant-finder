import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from urllib.parse import quote_plus, urlparse
from typing import Any, Dict, List, Optional, Tuple

from langchain.messages import AIMessage


GENERIC_CATEGORIES = {
    "restaurant",
    "restaurants",
    "cafe",
    "cafes",
    "coffee shop",
    "coffee shops",
    "food",
    "place",
    "places",
}

TAG_CATEGORY_PRIORITY = (
    "Highlights",
    "Popular for",
    "Planning",
    "Offerings",
    "Service options",
    "Atmosphere",
    "Amenities",
    "Dining options",
    "Parking",
    "Pets",
)

TAG_CATEGORY_WEIGHTS = {
    "Highlights": 100,
    "Popular for": 82,
    "Planning": 80,
    "Atmosphere": 72,
    "Offerings": 66,
    "Service options": 58,
    "Amenities": 44,
    "Dining options": 38,
    "Parking": 32,
    "Pets": 32,
    "Children": 24,
}

TAG_LABEL_NORMALIZATION = {
    "trending": "Trendy",
}

TAG_VARIANT_SUPPRESSION = {
    "cocktails": "great cocktails",
    "coffee": "great coffee",
    "wine": "great wine list",
    "dessert": "great dessert",
    "wi-fi": "free wi-fi",
}

TAG_LABEL_BONUSES = {
    "serves local specialty": 16,
    "great beer selection": 16,
    "rooftop seating": 16,
    "fireplace": 16,
    "live music": 12,
    "great coffee": 10,
    "great cocktails": 10,
    "great dessert": 9,
    "great wine list": 9,
    "fast service": 8,
    "quiet": 10,
    "private dining room": 12,
    "organic dishes": 12,
    "salad bar": 10,
    "prepared foods": 10,
    "quick bite": 10,
    "valet parking": 8,
    "dogs allowed inside": 8,
    "dogs allowed outside": 7,
    "dogs allowed": 6,
    "breakfast": 7,
    "brunch": 7,
    "brunch reservations recommended": 11,
    "lunch reservations recommended": 10,
    "dinner reservations recommended": 10,
    "reservations required": 12,
    "usually a wait": 9,
    "cozy": 4,
    "romantic": 5,
    "upscale": 6,
    "trendy": 4,
    "casual": 2,
}

TAG_LABEL_PENALTIES = {
    "lunch": 10,
    "dinner": 10,
    "solo dining": 12,
    "accepts reservations": 10,
    "dine-in": 14,
    "takeout": 13,
    "delivery": 13,
    "no-contact delivery": 11,
    "outdoor seating": 7,
    "onsite services": 14,
    "beer": 8,
    "wine": 8,
    "coffee": 8,
    "alcohol": 9,
    "vegetarian options": 5,
    "small plates": 4,
    "comfort food": 5,
    "dessert": 7,
    "counter service": 7,
    "catering": 6,
}

LOW_SIGNAL_TAGS = {
    "credit cards",
    "debit cards",
    "nfc mobile payments",
    "restroom",
    "wheelchair accessible entrance",
    "wheelchair accessible parking lot",
    "wheelchair accessible restroom",
    "wheelchair accessible seating",
    "seating",
    "table service",
    "groups",
    "tourists",
    "high chairs",
}


@dataclass(frozen=True)
class TagCandidate:
    display_label: str
    canonical_label: str
    category: str
    family: str
    category_priority: int
    source_index: int
    local_score: float


class FormatterAgent:
    """Deterministically normalize place results into the UI contract."""

    def __init__(self, default_city: str | None = None):
        self.default_city = default_city or os.getenv("DEFAULT_LOCATION", "Austin, TX")

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
    def _to_int(value: Any) -> Optional[int]:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            digits = re.sub(r"[^\d]", "", value)
            if not digits:
                return None
            try:
                return int(digits)
            except Exception:
                return None
        return None

    @staticmethod
    def _nested_get(item: Dict[str, Any], dotted_path: str) -> Any:
        cur: Any = item
        for part in dotted_path.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part)
        return cur

    @classmethod
    def _normalize_url(cls, value: Any) -> Optional[str]:
        text = cls._as_non_empty_string(value)
        if not text:
            return None

        markdown_match = re.match(r"^\[[^\]]+\]\((https?://[^)]+)\)$", text)
        if markdown_match:
            text = markdown_match.group(1)

        try:
            parsed = urlparse(text)
        except Exception:
            return None

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        return text

    @staticmethod
    def _format_info_link_markdown(link: str) -> str:
        safe_link = (link or "").strip()
        if not safe_link:
            return ""
        return f"[Visit site]({safe_link})"

    @staticmethod
    def _normalize_category_key(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.casefold())).strip()

    @classmethod
    def _is_generic_category(cls, value: str) -> bool:
        return cls._normalize_category_key(value) in GENERIC_CATEGORIES

    @classmethod
    def _normalize_categories(cls, item: Dict[str, Any]) -> List[str]:
        categories: List[str] = []
        seen: set[str] = set()
        raw_categories = item.get("categories")
        if isinstance(raw_categories, list):
            for entry in raw_categories:
                text = cls._as_non_empty_string(entry)
                if not text:
                    continue
                key = text.casefold()
                if key in seen:
                    continue
                seen.add(key)
                categories.append(text)

        category_name = cls._as_non_empty_string(item.get("categoryName"))
        if category_name and category_name.casefold() not in seen:
            categories.insert(0, category_name)
        return categories

    @classmethod
    def _normalize_detail(cls, item: Dict[str, Any]) -> str:
        category_name = cls._as_non_empty_string(item.get("categoryName"))
        categories = cls._normalize_categories(item)

        if category_name and not cls._is_generic_category(category_name):
            return category_name

        specific_categories = [
            category
            for category in categories
            if not cls._is_generic_category(category)
        ]
        if specific_categories:
            return ", ".join(specific_categories[:3])

        if category_name:
            return category_name

        if categories:
            return ", ".join(categories[:3])

        return (
            cls._first_non_empty(
                item.get("description"),
                item.get("caption"),
                item.get("detail"),
                "Restaurant",
            )
            or "Restaurant"
        )

    @classmethod
    def _normalize_score_text(cls, value: Any) -> Optional[str]:
        score = cls._to_float(value)
        if score is None:
            return None
        if score < 0 or score > 5:
            return None
        return f"{score:.1f}"

    @classmethod
    def _normalize_rating(cls, item: Dict[str, Any]) -> str:
        score_text = cls._normalize_score_text(item.get("totalScore"))
        if score_text is None:
            score_text = cls._normalize_score_text(item.get("rating"))

        reviews = cls._to_int(item.get("reviewsCount"))
        if score_text:
            return (
                f"{score_text} | {reviews} ratings"
                if reviews is not None
                else score_text
            )
        return f"{reviews} ratings" if reviews is not None else ""

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

        for candidate in (
            item.get("imageUrl"),
            item.get("imageURL"),
            self._nested_get(item, "photo.url"),
            item.get("thumbnail"),
            image_obj_url,
            item.get("photoUrl"),
        ):
            normalized = self._normalize_url(candidate)
            if normalized:
                return normalized
        return ""

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

            if lat is None or lng is None:
                continue
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                continue
            return lat, lng
        return None

    def _generate_maps_search_link(self, name: str, address: str) -> str:
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(f'{name} {address}')}"

    def _normalize_info_link(
        self, item: Dict[str, Any], name: str, address: str
    ) -> str:
        for candidate in (
            item.get("website"),
            item.get("url"),
            item.get("infoLink"),
            item.get("link"),
        ):
            normalized = self._normalize_url(candidate)
            if normalized:
                return normalized
        return self._generate_maps_search_link(name, address)

    @classmethod
    def _canonicalize_tag_label(cls, label: str) -> str:
        normalized = cls._as_non_empty_string(label) or ""
        if not normalized:
            return ""
        mapped = TAG_LABEL_NORMALIZATION.get(normalized.casefold())
        return mapped or normalized

    @classmethod
    def _tag_family(cls, category: str, label: str) -> str:
        canonical = label.casefold()
        if category == "Highlights":
            return "highlight"
        if category in {"Popular for", "Dining options"}:
            return "meal_occasion"
        if category == "Planning":
            return "planning"
        if category == "Atmosphere":
            return "vibe"
        if category == "Service options":
            return "service"
        if category == "Offerings":
            if canonical in {"vegetarian options", "organic dishes", "salad bar"}:
                return "menu_dietary"
            if canonical in {
                "cocktails",
                "great cocktails",
                "beer",
                "wine",
                "great wine list",
                "coffee",
                "great coffee",
            }:
                return "drink"
            return "menu_dietary"
        if category == "Pets":
            return "pets"
        if category == "Parking":
            return "parking"
        if category == "Amenities":
            return "amenity"
        if category == "Children":
            return "family"
        return "other"

    @classmethod
    def _is_low_signal_tag(cls, label: str, category: str) -> bool:
        canonical = label.casefold()
        if canonical in LOW_SIGNAL_TAGS:
            return True
        if category == "Payments":
            return True
        if category == "Accessibility":
            return True
        if category == "Amenities" and canonical in {
            "bar onsite",
            "restroom",
            "wi-fi",
            "free wi-fi",
        }:
            return True
        return False

    @classmethod
    def _collect_true_labels(cls, entries: Any) -> List[str]:
        if not isinstance(entries, list):
            return []

        labels: List[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for label, is_enabled in entry.items():
                if is_enabled is True:
                    text = cls._as_non_empty_string(label)
                    if text:
                        labels.append(text)
        return labels

    @classmethod
    def _tag_category_order(cls, additional_info: Dict[str, Any]) -> List[str]:
        ordered = list(TAG_CATEGORY_PRIORITY)
        for category in additional_info.keys():
            if category not in ordered:
                ordered.append(category)
        return ordered

    @classmethod
    def _score_tag_candidate(cls, category: str, canonical_label: str) -> float:
        score = float(TAG_CATEGORY_WEIGHTS.get(category, 24))
        score += float(TAG_LABEL_BONUSES.get(canonical_label, 0))
        score -= float(TAG_LABEL_PENALTIES.get(canonical_label, 0))
        return score

    def _extract_tag_candidates(self, item: Dict[str, Any]) -> List[TagCandidate]:
        additional_info = item.get("additionalInfo")
        if not isinstance(additional_info, dict):
            return []

        candidates_by_label: Dict[str, TagCandidate] = {}
        source_index = 0

        for category_priority, category in enumerate(
            self._tag_category_order(additional_info)
        ):
            for label in self._collect_true_labels(additional_info.get(category)):
                display_label = self._canonicalize_tag_label(label)
                if not display_label or self._is_low_signal_tag(
                    display_label, category
                ):
                    source_index += 1
                    continue

                canonical_label = display_label.casefold()
                candidate = TagCandidate(
                    display_label=display_label,
                    canonical_label=canonical_label,
                    category=category,
                    family=self._tag_family(category, display_label),
                    category_priority=category_priority,
                    source_index=source_index,
                    local_score=self._score_tag_candidate(category, canonical_label),
                )
                existing = candidates_by_label.get(canonical_label)
                if existing is None or (
                    candidate.local_score,
                    -candidate.category_priority,
                    -candidate.source_index,
                ) > (
                    existing.local_score,
                    -existing.category_priority,
                    -existing.source_index,
                ):
                    candidates_by_label[canonical_label] = candidate
                source_index += 1

        candidate_labels = set(candidates_by_label)
        for weaker_label, stronger_label in TAG_VARIANT_SUPPRESSION.items():
            if weaker_label in candidate_labels and stronger_label in candidate_labels:
                candidates_by_label.pop(weaker_label, None)

        return sorted(
            candidates_by_label.values(),
            key=lambda candidate: (
                -candidate.local_score,
                candidate.category_priority,
                candidate.source_index,
                candidate.canonical_label,
            ),
        )

    @staticmethod
    def _build_result_tag_stats(
        candidate_sets: List[List[TagCandidate]],
    ) -> Dict[str, Counter]:
        label_frequency: Counter[str] = Counter()
        family_frequency: Counter[str] = Counter()

        for candidates in candidate_sets:
            seen_labels: set[str] = set()
            seen_families: set[str] = set()
            for candidate in candidates:
                if candidate.canonical_label not in seen_labels:
                    label_frequency[candidate.canonical_label] += 1
                    seen_labels.add(candidate.canonical_label)
                if candidate.family not in seen_families:
                    family_frequency[candidate.family] += 1
                    seen_families.add(candidate.family)

        return {
            "label_frequency": label_frequency,
            "family_frequency": family_frequency,
        }

    @staticmethod
    def _rarity_bonus(label_frequency: int) -> float:
        if label_frequency <= 1:
            return 16.0
        if label_frequency == 2:
            return 11.0
        if label_frequency == 3:
            return 7.0
        if label_frequency == 4:
            return 4.0
        return 0.0

    def _select_visible_tags(
        self,
        candidates: List[TagCandidate],
        result_stats: Dict[str, Counter],
        label_exposure: Counter[str],
        pair_exposure: Counter[Tuple[str, str]],
        max_visible: int = 2,
    ) -> List[TagCandidate]:
        if not candidates or max_visible <= 0:
            return []

        ordered = sorted(
            candidates,
            key=lambda candidate: (
                -candidate.local_score,
                candidate.category_priority,
                candidate.source_index,
                candidate.canonical_label,
            ),
        )

        chosen = [ordered[0]]
        if max_visible == 1 or len(ordered) == 1:
            return chosen

        best_remaining_local_score = max(
            candidate.local_score for candidate in ordered[1:]
        )
        scored_candidates = []
        for candidate in ordered[1:]:
            adjusted_score = candidate.local_score
            adjusted_score += self._rarity_bonus(
                result_stats["label_frequency"].get(candidate.canonical_label, 0)
            )
            adjusted_score -= 6.0 * label_exposure.get(candidate.canonical_label, 0)
            adjusted_score -= 10.0 * pair_exposure.get(
                (chosen[0].canonical_label, candidate.canonical_label), 0
            )
            if candidate.family != chosen[0].family:
                adjusted_score += 8.0
            else:
                adjusted_score -= 8.0

            if candidate.local_score < best_remaining_local_score - 18.0:
                adjusted_score -= 8.0

            scored_candidates.append((adjusted_score, candidate))

        _, best_candidate = max(
            scored_candidates,
            key=lambda entry: (
                entry[0],
                entry[1].local_score,
                -entry[1].category_priority,
                -entry[1].source_index,
                entry[1].canonical_label,
            ),
        )
        chosen.append(best_candidate)
        return chosen

    def _select_fallback_tags(
        self,
        candidates: List[TagCandidate],
        chosen: List[TagCandidate],
        max_total: int = 3,
    ) -> List[TagCandidate]:
        if len(chosen) >= max_total:
            return chosen[:max_total]

        used_labels = {candidate.canonical_label for candidate in chosen}
        used_families = {candidate.family for candidate in chosen}
        remaining = [
            candidate
            for candidate in candidates
            if candidate.canonical_label not in used_labels
        ]
        if not remaining:
            return chosen

        best_candidate = max(
            remaining,
            key=lambda candidate: (
                candidate.local_score
                + (4.0 if candidate.family not in used_families else 0.0),
                candidate.local_score,
                -candidate.category_priority,
                -candidate.source_index,
                candidate.canonical_label,
            ),
        )
        return chosen + [best_candidate]

    @staticmethod
    def _serialize_tags(candidates: List[TagCandidate]) -> str:
        return " | ".join(candidate.display_label for candidate in candidates[:3])

    def _normalize_tags(self, item: Dict[str, Any]) -> str:
        candidates = self._extract_tag_candidates(item)
        if not candidates:
            return ""

        local_visible = self._select_visible_tags(
            candidates,
            self._build_result_tag_stats([candidates]),
            Counter(),
            Counter(),
        )
        all_tags = self._select_fallback_tags(candidates, local_visible, max_total=3)
        return self._serialize_tags(all_tags)

    def _assign_diversified_tags(
        self, normalized_items: List[Dict[str, Any]], raw_items: List[Dict[str, Any]]
    ) -> None:
        candidate_sets = [self._extract_tag_candidates(item) for item in raw_items]
        result_stats = self._build_result_tag_stats(candidate_sets)
        label_exposure: Counter[str] = Counter()
        pair_exposure: Counter[Tuple[str, str]] = Counter()

        for index, candidates in enumerate(candidate_sets):
            if index >= len(normalized_items):
                break
            if not candidates:
                continue

            visible_tags = self._select_visible_tags(
                candidates,
                result_stats,
                label_exposure,
                pair_exposure,
            )
            selected_tags = self._select_fallback_tags(
                candidates, visible_tags, max_total=3
            )
            normalized_items[index]["tags"] = self._serialize_tags(selected_tags)

            for candidate in visible_tags:
                label_exposure[candidate.canonical_label] += 1
            if len(visible_tags) >= 2:
                pair_exposure[
                    (visible_tags[0].canonical_label, visible_tags[1].canonical_label)
                ] += 1

    @classmethod
    def _build_restaurant_id(
        cls, item: Dict[str, Any], fallback_name: str, fallback_address: str
    ) -> str:
        for candidate in (
            item.get("placeId"),
            item.get("cid"),
            item.get("fid"),
            item.get("kgmid"),
            item.get("url"),
        ):
            text = cls._as_non_empty_string(candidate)
            if text:
                return text
        return f"{fallback_name.strip().lower()}::{fallback_address.strip().lower()}"

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        name = (
            self._first_non_empty(
                item.get("title"), item.get("name"), "Unknown restaurant"
            )
            or "Unknown restaurant"
        )
        detail = self._normalize_detail(item)
        address = self._normalize_address(item)
        info_link = self._normalize_info_link(item, name, address)
        restaurant_id = self._build_restaurant_id(item, name, address)

        normalized = {
            "restaurantId": restaurant_id,
            "name": name,
            "detail": detail,
            "rating": self._normalize_rating(item),
            "address": address,
            "imageUrl": self._normalize_image_url(item),
            "infoLink": info_link,
            "infoLinkMarkdown": self._format_info_link_markdown(info_link),
            "tags": self._normalize_tags(item),
        }

        reservation_url = self._normalize_url(item.get("reserveTableUrl"))
        if reservation_url:
            normalized["reservationUrl"] = reservation_url

        coords = self._extract_coords(item)
        if coords:
            normalized["lat"], normalized["lng"] = coords
        return normalized

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw Apify payload into the deterministic UI contract."""
        raw = str(state["messages"][-1].content)
        items: List[Dict[str, Any]] = []

        try:
            parsed_payload = json.loads(raw)
            items = self._extract_items(parsed_payload)
        except Exception:
            items = []

        normalized_items = [self._normalize_item(item) for item in items]
        self._assign_diversified_tags(normalized_items, items)
        return {
            "messages": state["messages"]
            + [AIMessage(content=json.dumps(normalized_items, ensure_ascii=False))]
        }
