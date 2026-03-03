import json
import os
from typing import Any, Dict, List

from langchain.agents import create_agent
from langchain_oci import ChatOCIGenAI
from langchain.messages import HumanMessage


FORMATTER_PROMPT = (
    "You normalize restaurant and cafe search results into a strict JSON array.\n"
    "Input: a JSON array of place objects from a web scraper (fields may vary).\n"
    "Output: ONLY a JSON array (no prose) where each element has exactly these keys: \n"
    "- name (string)\n"
    "- caption (string: short descriptor like cuisine or categories)\n"
    "- rating (string using Unicode stars such as '★★★★★', '★★★★☆', etc.)\n"
    "- location (string: formatted address or city)\n"
    "- imageURL (string: absolute URL to an image)\n"
    "- lat (number, optional)\n"
    "- lng (number, optional)\n"
    "- infoLink (string: https URL for more info)\n\n"
    "Rules:\n"
    "- If a numeric rating 0-5 exists, map to stars: >=4.5 '★★★★★', >=3.5 '★★★★☆', >=2.5 '★★★☆☆', >=1.5 '★★☆☆☆', >=0.5 '★☆☆☆☆', else '☆☆☆☆☆'.\n"
    "- caption: join up to 3 values from fields like categories/types/labels/cuisines if present; else short description.\n"
    "- infoLink: prefer website/url/link; otherwise create a Google Maps search link using the name and location.\n"
    "- imageURL: prefer photo.url/thumbnail/image/photoUrl if present; if none, omit the field or leave an empty string. Do not invent images.\n"
    "- location: prefer address/formattedAddress/fullAddress/vicinity/location; else fall back to provided default city if present.\n"
    "- lat/lng: if available in raw data as location/latitude/longitude/coords/geo, include numeric values (WGS84). If missing, omit keys.\n"
    "- Never include commentary or Markdown, only the JSON array.\n"
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

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes last message as raw JSON list; returns normalized JSON list as text.
        Also promotes nested coordinates (location.lat/lng) to top-level lat/lng when present.
        """
        # Promote coordinates deterministically so the map can always resolve them
        raw = state["messages"][-1].content
        raw_for_llm = raw
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                for it in data:
                    if isinstance(it, dict):
                        # Only read from location.lat/lng
                        loc = it.get("location")
                        if isinstance(loc, dict):
                            lat = loc.get("lat")
                            lng = loc.get("lng")
                            if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
                                it["lat"], it["lng"] = lat, lng
            raw_for_llm = json.dumps(data, ensure_ascii=False)
        except Exception:
            # If parsing fails, proceed with the original raw
            pass

        # Provide default city context inline for the model
        prompt = (
            f"DEFAULT_CITY: {self.default_city}\n"
            f"RAW_ITEMS_JSON: {raw_for_llm}\n"
            "Return ONLY the normalized JSON array as described."
        )
        result = await self._agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
        return result

