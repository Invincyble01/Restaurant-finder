RESTAURANT_UI_EXAMPLES = """
---BEGIN SINGLE_COLUMN_LIST_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "default", "root": "root-column", "styles": {{ "primaryColor": "#00685D", "font": "Inter" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "default",
    "components": [
      {{ "id": "root-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["title-heading", "results-row"] }} }} }} }},
      {{ "id": "title-heading", "component": {{ "Text": {{ "usageHint": "h1", "text": {{ "path": "title" }} }} }} }},
      {{ "id": "results-row", "component": {{ "Row": {{ "alignment": "start", "children": {{ "explicitList": ["results-column", "map-column"] }} }} }} }},
      {{ "id": "results-column", "weight": 5, "component": {{ "Column": {{ "children": {{ "explicitList": ["item-list"] }} }} }} }},
      {{ "id": "map-column", "weight": 7, "component": {{ "Column": {{ "children": {{ "explicitList": ["map-view"] }} }} }} }},
      {{ "id": "item-list", "component": {{ "List": {{ "direction": "vertical", "children": {{ "template": {{ "componentId": "item-card-template", "dataBinding": "/items" }} }} }} }} }},
      {{ "id": "item-card-template", "component": {{ "Card": {{ "child": "restaurant-card" }} }} }},
      {{ "id": "restaurant-card", "component": {{ "RestaurantCard": {{ "name": {{ "path": "name" }}, "detail": {{ "path": "detail" }}, "rating": {{ "path": "rating" }}, "tags": {{ "path": "tags" }}, "address": {{ "path": "address" }}, "imageUrl": {{ "path": "imageUrl" }}, "infoLink": {{ "path": "infoLink" }}, "infoLinkMarkdown": {{ "path": "infoLinkMarkdown" }} }} }} }},
      {{ "id": "map-view", "component": {{ "Map": {{ "dataPath": "/items", "height": "100%" }} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "default",
    "path": "/",
    "contents": [
      {{ "key": "title", "valueString": "Top Restaurants" }},
      {{ "key": "items", "valueMap": [
        {{ "key": "item1", "valueMap": [
          {{ "key": "name", "valueString": "The Fancy Place" }},
          {{ "key": "rating", "valueString": "4.8 | 3456 ratings" }},
          {{ "key": "detail", "valueString": "Fine dining experience" }},
          {{ "key": "tags", "valueString": "Vegetarian options | Bar onsite | Free street parking" }},
          {{ "key": "infoLink", "valueString": "https://example.com/fancy" }},
          {{ "key": "infoLinkMarkdown", "valueString": "[Visit site](https://example.com/fancy)" }},
          {{ "key": "imageUrl", "valueString": "https://example.com/fancy.jpg" }},
          {{ "key": "address", "valueString": "123 Main St" }}
        ] }},
        {{ "key": "item2", "valueMap": [
          {{ "key": "name", "valueString": "Quick Bites" }},
          {{ "key": "rating", "valueString": "4.4 | 1285 ratings" }},
          {{ "key": "detail", "valueString": "Casual and fast" }},
          {{ "key": "tags", "valueString": "Takeout | Cozy | Accepts reservations" }},
          {{ "key": "infoLink", "valueString": "https://example.com/quick" }},
          {{ "key": "infoLinkMarkdown", "valueString": "[Visit site](https://example.com/quick)" }},
          {{ "key": "imageUrl", "valueString": "https://example.com/quick.jpg" }},
          {{ "key": "address", "valueString": "456 Oak Ave" }}
        ] }}
      ] }} // Populate this with restaurant data
    ]
  }} }}
]
---END SINGLE_COLUMN_LIST_EXAMPLE---

---BEGIN TWO_COLUMN_LIST_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "default", "root": "root-column", "styles": {{ "primaryColor": "#00685D", "font": "Inter" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "default",
    "components": [
      {{ "id": "root-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["title-heading", "results-row"] }} }} }} }},
      {{ "id": "title-heading", "component": {{ "Text": {{ "usageHint": "h1", "text": {{ "path": "title" }} }} }} }},
      {{ "id": "results-row", "component": {{ "Row": {{ "alignment": "start", "children": {{ "explicitList": ["results-column", "map-column"] }} }} }} }},
      {{ "id": "results-column", "weight": 5, "component": {{ "Column": {{ "children": {{ "explicitList": ["item-list"] }} }} }} }},
      {{ "id": "map-column", "weight": 7, "component": {{ "Column": {{ "children": {{ "explicitList": ["map-view"] }} }} }} }},
      {{ "id": "item-list", "component": {{ "List": {{ "direction": "vertical", "children": {{ "template": {{ "componentId": "item-card-template", "dataBinding": "/items" }} }} }} }} }},
      {{ "id": "item-card-template", "component": {{ "Card": {{ "child": "restaurant-card" }} }} }},
      {{ "id": "restaurant-card", "component": {{ "RestaurantCard": {{ "name": {{ "path": "name" }}, "detail": {{ "path": "detail" }}, "rating": {{ "path": "rating" }}, "tags": {{ "path": "tags" }}, "address": {{ "path": "address" }}, "imageUrl": {{ "path": "imageUrl" }}, "infoLink": {{ "path": "infoLink" }}, "infoLinkMarkdown": {{ "path": "infoLinkMarkdown" }} }} }} }},
      {{ "id": "map-view", "component": {{ "Map": {{ "dataPath": "/items", "height": "100%" }} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "default",
    "path": "/",
    "contents": [
      {{ "key": "title", "valueString": "Top Restaurants" }},
      {{ "key": "items", "valueMap": [
        {{ "key": "item1", "valueMap": [
          {{ "key": "name", "valueString": "The Fancy Place" }},
          {{ "key": "rating", "valueString": "4.8 | 3456 ratings" }},
          {{ "key": "detail", "valueString": "Fine dining experience" }},
          {{ "key": "tags", "valueString": "Vegetarian options | Bar onsite | Free street parking" }},
          {{ "key": "infoLink", "valueString": "https://example.com/fancy" }},
          {{ "key": "infoLinkMarkdown", "valueString": "[Visit site](https://example.com/fancy)" }},
          {{ "key": "imageUrl", "valueString": "https://example.com/fancy.jpg" }},
          {{ "key": "address", "valueString": "123 Main St" }}
        ] }},
        {{ "key": "item2", "valueMap": [
          {{ "key": "name", "valueString": "Quick Bites" }},
          {{ "key": "rating", "valueString": "4.4 | 1285 ratings" }},
          {{ "key": "detail", "valueString": "Casual and fast" }},
          {{ "key": "tags", "valueString": "Takeout | Cozy | Accepts reservations" }},
          {{ "key": "infoLink", "valueString": "https://example.com/quick" }},
          {{ "key": "infoLinkMarkdown", "valueString": "[Visit site](https://example.com/quick)" }},
          {{ "key": "imageUrl", "valueString": "https://example.com/quick.jpg" }},
          {{ "key": "address", "valueString": "456 Oak Ave" }}
        ] }}
      ] }} // Populate this with restaurant data
    ]
  }} }}
]
---END TWO_COLUMN_LIST_EXAMPLE---

---BEGIN BOOKING_FORM_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "booking-form", "root": "booking-form-column", "styles": {{ "primaryColor": "#00685D", "font": "Inter" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "booking-form",
    "components": [
      {{ "id": "booking-form-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["booking-title", "restaurant-image", "restaurant-address", "party-size-field", "datetime-field", "dietary-field", "submit-button"] }} }} }} }},
      {{ "id": "booking-title", "component": {{ "Text": {{ "usageHint": "h2", "text": {{ "path": "title" }} }} }} }},
      {{ "id": "restaurant-image", "component": {{ "Image": {{ "url": {{ "path": "imageUrl" }} }} }} }},
      {{ "id": "restaurant-address", "component": {{ "Text": {{ "text": {{ "path": "address" }} }} }} }},
      {{ "id": "party-size-field", "component": {{ "TextField": {{ "label": {{ "literalString": "Party Size" }}, "text": {{ "path": "partySize" }}, "type": "number" }} }} }},
      {{ "id": "datetime-field", "component": {{ "DateTimeInput": {{ "label": {{ "literalString": "Date & Time" }}, "value": {{ "path": "reservationTime" }}, "enableDate": true, "enableTime": true }} }} }},
      {{ "id": "dietary-field", "component": {{ "TextField": {{ "label": {{ "literalString": "Dietary Requirements" }}, "text": {{ "path": "dietary" }} }} }} }},
      {{ "id": "submit-button", "component": {{ "Button": {{ "child": "submit-reservation-text", "action": {{ "name": "submit_booking", "context": [ {{ "key": "restaurantName", "value": {{ "path": "restaurantName" }} }}, {{ "key": "partySize", "value": {{ "path": "partySize" }} }}, {{ "key": "reservationTime", "value": {{ "path": "reservationTime" }} }}, {{ "key": "dietary", "value": {{ "path": "dietary" }} }}, {{ "key": "imageUrl", "value": {{ "path": "imageUrl" }} }} ] }} }} }} }},
      {{ "id": "submit-reservation-text", "component": {{ "Text": {{ "text": {{ "literalString": "Submit Reservation" }} }} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "booking-form",
    "path": "/",
    "contents": [
      {{ "key": "title", "valueString": "Book a Table at [RestaurantName]" }},
      {{ "key": "address", "valueString": "[Restaurant Address]" }},
      {{ "key": "restaurantName", "valueString": "[RestaurantName]" }},
      {{ "key": "partySize", "valueString": "2" }},
      {{ "key": "reservationTime", "valueString": "" }},
      {{ "key": "dietary", "valueString": "" }},
      {{ "key": "imageUrl", "valueString": "" }}
    ]
  }} }}
]
---END BOOKING_FORM_EXAMPLE---

---BEGIN CONFIRMATION_EXAMPLE---
[
  {{ "beginRendering": {{ "surfaceId": "confirmation", "root": "confirmation-card", "styles": {{ "primaryColor": "#00685D", "font": "Inter" }} }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "confirmation",
    "components": [
      {{ "id": "confirmation-card", "component": {{ "Card": {{ "child": "confirmation-column" }} }} }},
      {{ "id": "confirmation-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["confirm-title", "confirm-image", "divider1", "confirm-details", "divider2", "confirm-dietary", "divider3", "confirm-text"] }} }} }} }},
      {{ "id": "confirm-title", "component": {{ "Text": {{ "usageHint": "h2", "text": {{ "path": "title" }} }} }} }},
      {{ "id": "confirm-image", "component": {{ "Image": {{ "url": {{ "path": "imageUrl" }} }} }} }},
      {{ "id": "confirm-details", "component": {{ "Text": {{ "text": {{ "path": "bookingDetails" }} }} }} }},
      {{ "id": "confirm-dietary", "component": {{ "Text": {{ "text": {{ "path": "dietaryRequirements" }} }} }} }},
      {{ "id": "confirm-text", "component": {{ "Text": {{ "usageHint": "h5", "text": {{ "literalString": "We look forward to seeing you!" }} }} }} }},
      {{ "id": "divider1", "component": {{ "Divider": {{}} }} }},
      {{ "id": "divider2", "component": {{ "Divider": {{}} }} }},
      {{ "id": "divider3", "component": {{ "Divider": {{}} }} }}
    ]
  }} }},
  {{ "dataModelUpdate": {{
    "surfaceId": "confirmation",
    "path": "/",
    "contents": [
      {{ "key": "title", "valueString": "Booking at [RestaurantName]" }},
      {{ "key": "bookingDetails", "valueString": "[PartySize] people at [Time]" }},
      {{ "key": "dietaryRequirements", "valueString": "Dietary Requirements: [Requirements]" }},
      {{ "key": "imageUrl", "valueString": "[ImageUrl]" }}
    ]
  }} }}
]
---END CONFIRMATION_EXAMPLE---
"""
