import copy
import json
import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from agent.graph.struct import PresenterOutput


RESULTS_SURFACE_ID = "default"
BOOKING_SURFACE_ID = "booking-form"
CONFIRMATION_SURFACE_ID = "confirmation"
PRIMARY_COLOR = "#00685D"
FONT_NAME = "Inter"

BOOK_REQUEST_PREFIX = "USER_WANTS_TO_BOOK:"
BOOK_SUBMISSION_PREFIX = "User submitted a booking for "


RESULTS_COMPONENTS = [
    {
        "id": "root-column",
        "component": {
            "Column": {"children": {"explicitList": ["title-heading", "results-row"]}}
        },
    },
    {
        "id": "title-heading",
        "component": {"Text": {"usageHint": "h1", "text": {"path": "title"}}},
    },
    {
        "id": "results-row",
        "component": {
            "Row": {
                "alignment": "start",
                "children": {"explicitList": ["results-column", "map-column"]},
            }
        },
    },
    {
        "id": "results-column",
        "weight": 5,
        "component": {"Column": {"children": {"explicitList": ["item-list"]}}},
    },
    {
        "id": "map-column",
        "weight": 7,
        "component": {"Column": {"children": {"explicitList": ["map-view"]}}},
    },
    {
        "id": "item-list",
        "component": {
            "List": {
                "direction": "vertical",
                "children": {
                    "template": {
                        "componentId": "item-card-template",
                        "dataBinding": "/items",
                    }
                },
            }
        },
    },
    {
        "id": "item-card-template",
        "component": {"Card": {"child": "restaurant-card"}},
    },
    {
        "id": "restaurant-card",
        "component": {
            "RestaurantCard": {
                "name": {"path": "name"},
                "detail": {"path": "detail"},
                "rating": {"path": "rating"},
                "tags": {"path": "tags"},
                "address": {"path": "address"},
                "imageUrl": {"path": "imageUrl"},
                "infoLink": {"path": "infoLink"},
                "infoLinkMarkdown": {"path": "infoLinkMarkdown"},
            }
        },
    },
    {
        "id": "map-view",
        "component": {"Map": {"dataPath": "/items", "height": "100%"}},
    },
]


BOOKING_COMPONENTS = [
    {
        "id": "booking-form-column",
        "component": {
            "Column": {
                "children": {
                    "explicitList": [
                        "booking-title",
                        "restaurant-image",
                        "restaurant-address",
                        "party-size-field",
                        "datetime-field",
                        "dietary-field",
                        "submit-button",
                    ]
                }
            }
        },
    },
    {
        "id": "booking-title",
        "component": {"Text": {"usageHint": "h2", "text": {"path": "title"}}},
    },
    {
        "id": "restaurant-image",
        "component": {"Image": {"url": {"path": "imageUrl"}}},
    },
    {
        "id": "restaurant-address",
        "component": {"Text": {"text": {"path": "address"}}},
    },
    {
        "id": "party-size-field",
        "component": {
            "TextField": {
                "label": {"literalString": "Party Size"},
                "text": {"path": "partySize"},
                "type": "number",
            }
        },
    },
    {
        "id": "datetime-field",
        "component": {
            "DateTimeInput": {
                "label": {"literalString": "Date & Time"},
                "value": {"path": "reservationTime"},
                "enableDate": True,
                "enableTime": True,
            }
        },
    },
    {
        "id": "dietary-field",
        "component": {
            "TextField": {
                "label": {"literalString": "Dietary Requirements"},
                "text": {"path": "dietary"},
            }
        },
    },
    {
        "id": "submit-button",
        "component": {
            "Button": {
                "child": "submit-reservation-text",
                "action": {
                    "name": "submit_booking",
                    "context": [
                        {"key": "restaurantName", "value": {"path": "restaurantName"}},
                        {"key": "partySize", "value": {"path": "partySize"}},
                        {
                            "key": "reservationTime",
                            "value": {"path": "reservationTime"},
                        },
                        {"key": "dietary", "value": {"path": "dietary"}},
                        {"key": "imageUrl", "value": {"path": "imageUrl"}},
                    ],
                },
            }
        },
    },
    {
        "id": "submit-reservation-text",
        "component": {"Text": {"text": {"literalString": "Submit Reservation"}}},
    },
]


CONFIRMATION_COMPONENTS = [
    {
        "id": "confirmation-card",
        "component": {"Card": {"child": "confirmation-column"}},
    },
    {
        "id": "confirmation-column",
        "component": {
            "Column": {
                "children": {
                    "explicitList": [
                        "confirm-title",
                        "confirm-image",
                        "divider1",
                        "confirm-details",
                        "divider2",
                        "confirm-dietary",
                        "divider3",
                        "confirm-text",
                    ]
                }
            }
        },
    },
    {
        "id": "confirm-title",
        "component": {"Text": {"usageHint": "h2", "text": {"path": "title"}}},
    },
    {
        "id": "confirm-image",
        "component": {"Image": {"url": {"path": "imageUrl"}}},
    },
    {
        "id": "confirm-details",
        "component": {"Text": {"text": {"path": "bookingDetails"}}},
    },
    {
        "id": "confirm-dietary",
        "component": {"Text": {"text": {"path": "dietaryRequirements"}}},
    },
    {
        "id": "confirm-text",
        "component": {
            "Text": {
                "usageHint": "h5",
                "text": {"literalString": "We look forward to seeing you!"},
            }
        },
    },
    {"id": "divider1", "component": {"Divider": {}}},
    {"id": "divider2", "component": {"Divider": {}}},
    {"id": "divider3", "component": {"Divider": {}}},
]


def is_booking_request(query: str) -> bool:
    return (query or "").startswith(BOOK_REQUEST_PREFIX)


def is_booking_submission(query: str) -> bool:
    return (query or "").startswith(BOOK_SUBMISSION_PREFIX)


def build_ui_output(text: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    return asdict(
        PresenterOutput(kind="ui", text=(text or "").strip(), a2ui_messages=messages)
    )


def build_text_output(text: str) -> Dict[str, Any]:
    return asdict(PresenterOutput(kind="text", text=(text or "").strip()))


def build_results_surface(
    items: List[Dict[str, Any]], title: str = "Top Restaurants"
) -> List[Dict[str, Any]]:
    safe_items = [copy.deepcopy(item) for item in items]
    return [
        {
            "beginRendering": {
                "surfaceId": RESULTS_SURFACE_ID,
                "root": "root-column",
                "styles": {"primaryColor": PRIMARY_COLOR, "font": FONT_NAME},
            }
        },
        {
            "surfaceUpdate": {
                "surfaceId": RESULTS_SURFACE_ID,
                "components": copy.deepcopy(RESULTS_COMPONENTS),
            }
        },
        {
            "dataModelUpdate": {
                "surfaceId": RESULTS_SURFACE_ID,
                "path": "/",
                "contents": [{"key": "title", "valueString": title}],
            }
        },
        {
            "dataModelUpdate": {
                "surfaceId": RESULTS_SURFACE_ID,
                "path": "/items",
                "contents": [
                    {
                        "key": ".",
                        "valueString": json.dumps(safe_items, ensure_ascii=False),
                    }
                ],
            }
        },
    ]


def build_booking_form_surface(
    restaurant_name: str,
    address: str = "",
    image_url: str = "",
) -> List[Dict[str, Any]]:
    return [
        {
            "beginRendering": {
                "surfaceId": BOOKING_SURFACE_ID,
                "root": "booking-form-column",
                "styles": {"primaryColor": PRIMARY_COLOR, "font": FONT_NAME},
            }
        },
        {
            "surfaceUpdate": {
                "surfaceId": BOOKING_SURFACE_ID,
                "components": copy.deepcopy(BOOKING_COMPONENTS),
            }
        },
        {
            "dataModelUpdate": {
                "surfaceId": BOOKING_SURFACE_ID,
                "path": "/",
                "contents": [
                    {
                        "key": "title",
                        "valueString": f"Book a Table at {restaurant_name}",
                    },
                    {"key": "address", "valueString": address},
                    {"key": "restaurantName", "valueString": restaurant_name},
                    {"key": "partySize", "valueString": "2"},
                    {"key": "reservationTime", "valueString": ""},
                    {"key": "dietary", "valueString": ""},
                    {"key": "imageUrl", "valueString": image_url},
                ],
            }
        },
    ]


def build_confirmation_surface(
    restaurant_name: str,
    party_size: str,
    reservation_time: str,
    dietary: str,
    image_url: str = "",
) -> List[Dict[str, Any]]:
    dietary_requirements = dietary.strip() or "None"
    return [
        {
            "beginRendering": {
                "surfaceId": CONFIRMATION_SURFACE_ID,
                "root": "confirmation-card",
                "styles": {"primaryColor": PRIMARY_COLOR, "font": FONT_NAME},
            }
        },
        {
            "surfaceUpdate": {
                "surfaceId": CONFIRMATION_SURFACE_ID,
                "components": copy.deepcopy(CONFIRMATION_COMPONENTS),
            }
        },
        {
            "dataModelUpdate": {
                "surfaceId": CONFIRMATION_SURFACE_ID,
                "path": "/",
                "contents": [
                    {"key": "title", "valueString": f"Booking at {restaurant_name}"},
                    {
                        "key": "bookingDetails",
                        "valueString": f"{party_size} people at {reservation_time}",
                    },
                    {
                        "key": "dietaryRequirements",
                        "valueString": f"Dietary Requirements: {dietary_requirements}",
                    },
                    {"key": "imageUrl", "valueString": image_url},
                ],
            }
        },
    ]


def build_results_text(items: List[Dict[str, Any]]) -> str:
    if not items:
        return (
            "I could not find matching restaurants for that request right now. "
            "Try another cuisine, city, or dining style."
        )

    count = len(items)
    names = [
        str(item.get("name", "")).strip() for item in items[:3] if item.get("name")
    ]
    if not names:
        return f"I found {count} restaurants that match your request."

    if count == 1:
        return f"I found 1 restaurant that matches your request: {names[0]}."

    lead = ", ".join(names[:-1]) + f" and {names[-1]}" if len(names) > 1 else names[0]
    return f"I found {count} restaurants that match your request, including {lead}."


def build_booking_text(restaurant_name: str) -> str:
    return f"Let's book a table at {restaurant_name}. I've prepared the reservation form for you."


def build_confirmation_text(restaurant_name: str) -> str:
    return f"Your reservation details for {restaurant_name} are ready below."


def parse_booking_request(query: str) -> Dict[str, str]:
    payload = (query or "").removeprefix(BOOK_REQUEST_PREFIX).strip()
    restaurant_name = payload
    address = ""
    image_url = ""

    address_marker = ", Address:"
    image_marker = ", ImageURL:"
    if address_marker in payload:
        restaurant_name, remainder = payload.split(address_marker, 1)
        restaurant_name = restaurant_name.strip()
        remainder = remainder.strip()
        if image_marker.strip() in remainder:
            address, image_url = remainder.split(image_marker.strip(), 1)
            address = address.strip().rstrip(",")
            image_url = image_url.strip()
        else:
            address = remainder.strip()
    elif image_marker in payload:
        restaurant_name, image_url = payload.split(image_marker, 1)
        restaurant_name = restaurant_name.strip().rstrip(",")
        image_url = image_url.strip()

    return {
        "restaurant_name": restaurant_name or "Selected restaurant",
        "address": address,
        "image_url": image_url,
    }


def parse_booking_submission(query: str) -> Dict[str, str]:
    pattern = re.compile(
        r"^User submitted a booking for (?P<restaurant>.+?) for (?P<party_size>.+?) people at (?P<reservation_time>.+?) with dietary requirements: (?P<dietary>.*?)(?:\. The image URL is (?P<image_url>.*))?$"
    )
    match = pattern.match((query or "").strip())
    if match:
        groups = match.groupdict()
        return {
            "restaurant_name": (
                groups.get("restaurant") or "Selected restaurant"
            ).strip(),
            "party_size": (groups.get("party_size") or "2").strip(),
            "reservation_time": (groups.get("reservation_time") or "Soon").strip(),
            "dietary": (groups.get("dietary") or "None").strip(),
            "image_url": (groups.get("image_url") or "").strip(),
        }

    trimmed = (query or "").strip()
    return {
        "restaurant_name": trimmed.removeprefix(BOOK_SUBMISSION_PREFIX).strip()
        or "Selected restaurant",
        "party_size": "2",
        "reservation_time": "Soon",
        "dietary": "None",
        "image_url": "",
    }
