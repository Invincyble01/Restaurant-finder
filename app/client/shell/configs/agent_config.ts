import { EnhancedAgentAppConfig, ToolAssignments } from "./types.js";

const agents = {
  "apify_places_agent": {
    model: "xai.grok-4-fast-non-reasoning",
    temperature: 0.3,
    name: "apify_places_agent",
    systemPrompt: "You find restaurants and cafes using an MCP tool. Always call the discovered Google Places tool with the user's text as a single-element 'queries' array and 'maxItems' from the text (default 5). Return ONLY the tool JSON.",
    toolsEnabled: ["compass/crawler-google-places"]
  },
  "formatter_agent": {
    model: "openai.gpt-4.1",
    temperature: 0.2,
    name: "formatter_agent",
    systemPrompt: "Normalize raw place items to an array of {name, caption, rating, location, imageURL, infoLink}. Return JSON only.",
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
