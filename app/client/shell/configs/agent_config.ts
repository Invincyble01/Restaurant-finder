import { EnhancedAgentAppConfig, ToolAssignments } from "./types.js";

const agents = {
  "apify_places_agent": {
    model: "xai.grok-4-fast-non-reasoning",
    temperature: 0.3,
    name: "apify_places_agent",
    systemPrompt: "You find restaurants and cafes using the Apify crawler-google-places schema. Prefer searchStringsArray + locationQuery (or startUrls/placeIds when present), set maxCrawledPlacesPerSearch from the user's count (default 5), and return only tool JSON.",
    toolsEnabled: ["compass/crawler-google-places"]
  },
  "formatter_agent": {
    model: "openai.gpt-4.1",
    temperature: 0.2,
    name: "formatter_agent",
    systemPrompt: "Normalize raw place items to an array of {name, detail, rating, address, imageUrl, infoLink, infoLinkMarkdown, lat?, lng?}. Include reviewsCount in rating display when available (e.g., '★★★★★ | 3456 ratings'). Prefer Apify raw fields like title/categoryName/totalScore/address/imageUrl/website.",
    toolsEnabled: []
  },
  "presenter_agent": {
    model: "xai.grok-4-fast-non-reasoning",
    temperature: 0.7,
    name: "presenter_agent",
    systemPrompt: "",
    toolsEnabled: []
  }
};

const toolAssignments: ToolAssignments = {
  // Not used by the new server graph, kept for UI config canvas
  "get_restaurants": "apify_places_agent",
  "get_cafes": "apify_places_agent",
  "get_restaurant_data": "formatter_agent",
  "get_cafe_data": "formatter_agent"
};

export const agentConfig: EnhancedAgentAppConfig = {
  agents,
  toolAssignments
};
