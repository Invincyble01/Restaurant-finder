from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Data class for better json handling
@dataclass
class AgentConfig:
    """Configuration for an agent"""

    model: str
    temperature: float
    name: str
    system_prompt: Optional[str]
    tools_enabled: List[str]


@dataclass
class PresenterOutput:
    """Structured final output emitted by the presenter path."""

    kind: str
    text: str
    a2ui_messages: List[Dict[str, Any]] = field(default_factory=list)


# JSON Schema for validating AgentConfig
AGENT_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "model": {"type": "string"},
        "temperature": {"type": "number", "minimum": 0, "maximum": 2},
        "name": {"type": "string"},
        "system_prompt": {"type": ["string", "null"]},
        "tools_enabled": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["model", "temperature", "name", "tools_enabled"],
}

CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "apify_places_agent": AGENT_CONFIG_SCHEMA,
        "formatter_agent": AGENT_CONFIG_SCHEMA,
        "presenter_agent": AGENT_CONFIG_SCHEMA,
    },
    "additionalProperties": False,
}

# Default agent config
DEFAULT_CONFIG = {
    "apify_places_agent": AgentConfig(
        model="xai.grok-4-fast-non-reasoning",
        temperature=0.3,
        name="apify_places_agent",
        system_prompt=(
            "You find restaurants and cafes using the configured Apify data provider.\n"
            "- Convert the user's request into valid Google Maps actor input.\n"
            "- Extract numeric count from the query; default 5.\n"
            "- Return ONLY the raw JSON array string for downstream formatting."
        ),
        tools_enabled=["compass/crawler-google-places"],
    ),
    "formatter_agent": AgentConfig(
        model="openai.gpt-4.1",
        temperature=0.2,
        name="formatter_agent",
        system_prompt=None,
        tools_enabled=[],
    ),
    "presenter_agent": AgentConfig(
        model="xai.grok-4",
        temperature=0.7,
        name="presenter_agent",
        system_prompt=None,
        tools_enabled=[],
    ),
}


# Exception for the config graph
class RestaurantGraphException(Exception):
    """Exception for missing graph configs"""

    def __init__(self, message="Missing configuration dictionary for graph"):
        self.message = message
        super().__init__(self.message)
