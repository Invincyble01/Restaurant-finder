import json
import logging
import os
import re
from dataclasses import asdict
from typing import Any, Dict, List
from langchain.agents import create_agent
from langchain_oci import ChatOCIGenAI
from langchain.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph
from dotenv import load_dotenv

load_dotenv()

import jsonschema
from agent.prompt_builder import (
    A2UI_SCHEMA,
    get_text_prompt,
)
from agent.graph.struct import AgentConfig, PresenterOutput
from agent.graph.a2ui_builder import (
    build_booking_form_surface,
    build_booking_text,
    build_confirmation_surface,
    build_confirmation_text,
    build_results_surface,
    build_results_text,
    build_text_output,
    build_ui_output,
    is_booking_request,
    is_booking_submission,
    parse_booking_request,
    parse_booking_submission,
)

logger = logging.getLogger(__name__)


class PresenterAgent:
    """Agent that generates A2UI schemas from restaurant data"""

    def __init__(self, base_url: str, use_ui: bool = False, config: AgentConfig = None):
        if config:
            self.oci_model = config.model
            self.model_temperature = config.temperature
            self.agent_name = config.name
        else:
            self.oci_model = "xai.grok-4"
            self.model_temperature = 0.7
            self.agent_name = "presenter_agent"
        self.base_url = base_url
        self.use_ui = use_ui
        self._agent = None if self.use_ui else self._build_agent()

        # Load the A2UI_SCHEMA string into a Python object for validation
        try:
            # First, load the schema for a *single message*
            single_message_schema = json.loads(A2UI_SCHEMA)

            # The prompt instructs the LLM to return a *list* of messages.
            # Therefore, our validation schema must be an *array* of the single message schema.
            self.a2ui_schema_object = {"type": "array", "items": single_message_schema}
            logger.info(
                "A2UI_SCHEMA successfully loaded and wrapped in an array validator."
            )
        except json.JSONDecodeError as e:
            logger.error(f"CRITICAL: Failed to parse A2UI_SCHEMA: {e}")
            self.a2ui_schema_object = None

    def _build_agent(self) -> CompiledStateGraph:
        """Builds the agent for the presenter."""
        instruction = get_text_prompt()

        oci_llm = ChatOCIGenAI(
            model_id=self.oci_model,
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs={"temperature": self.model_temperature},
            auth_profile=os.getenv("AUTH_PROFILE"),
        )

        return create_agent(
            model=oci_llm, tools=[], system_prompt=instruction, name=self.agent_name
        )

    def _validate_ui_messages(self, messages: List[Dict[str, Any]]) -> None:
        if self.a2ui_schema_object is None:
            raise ValueError("A2UI schema is not loaded")
        jsonschema.validate(instance=messages, schema=self.a2ui_schema_object)

    @staticmethod
    def _coerce_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

    @staticmethod
    def _build_ai_message(
        output: PresenterOutput | Dict[str, Any],
        name: str,
        response_metadata: Dict[str, Any] | None = None,
    ) -> AIMessage:
        presenter_output = (
            asdict(output) if isinstance(output, PresenterOutput) else dict(output)
        )
        return AIMessage(
            content=presenter_output.get("text", ""),
            name=name,
            response_metadata=response_metadata or {},
            additional_kwargs={"presenter_output": presenter_output},
        )

    def _build_results_response(self, formatter_payload: str) -> Dict[str, Any]:
        formatter_items: List[Dict[str, Any]] = []
        try:
            parsed = json.loads(formatter_payload)
            if isinstance(parsed, list):
                formatter_items = [
                    self._canonicalize_formatter_item(it)
                    for it in parsed
                    if isinstance(it, dict)
                ]
        except Exception:
            formatter_items = []

        ui_messages = build_results_surface(formatter_items)
        self._validate_ui_messages(ui_messages)
        return build_ui_output(build_results_text(formatter_items), ui_messages)

    def _build_booking_response(self, query: str) -> Dict[str, Any]:
        booking_data = parse_booking_request(query)
        ui_messages = build_booking_form_surface(
            booking_data["restaurant_name"],
            booking_data.get("address", ""),
            booking_data.get("image_url", ""),
        )
        self._validate_ui_messages(ui_messages)
        return build_ui_output(
            build_booking_text(booking_data["restaurant_name"]), ui_messages
        )

    def _build_confirmation_response(self, query: str) -> Dict[str, Any]:
        confirmation_data = parse_booking_submission(query)
        ui_messages = build_confirmation_surface(
            confirmation_data["restaurant_name"],
            confirmation_data["party_size"],
            confirmation_data["reservation_time"],
            confirmation_data["dietary"],
            confirmation_data.get("image_url", ""),
        )
        self._validate_ui_messages(ui_messages)
        return build_ui_output(
            build_confirmation_text(confirmation_data["restaurant_name"]), ui_messages
        )

    def _build_deterministic_ui_response(self, data: str) -> Dict[str, Any]:
        if is_booking_request(data):
            return self._build_booking_response(data)
        if is_booking_submission(data):
            return self._build_confirmation_response(data)
        return self._build_results_response(data)

    @staticmethod
    def _as_non_empty_string(value):
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text if text else None
        text = str(value).strip()
        return text if text else None

    @classmethod
    def _coalesce(cls, *values):
        for value in values:
            text = cls._as_non_empty_string(value)
            if text:
                return text
        return None

    @staticmethod
    def _extract_info_link(value):
        if not value:
            return None

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None

            markdown_match = re.match(r"^\[[^\]]+\]\((https?://[^)]+)\)$", text)
            if markdown_match:
                return markdown_match.group(1)

            return text

        return None

    @staticmethod
    def _format_info_link_markdown(link):
        safe_link = (link or "").strip()
        if not safe_link:
            return ""
        return f"[Visit site]({safe_link})"

    @classmethod
    def _canonicalize_formatter_item(cls, item):
        if not isinstance(item, dict):
            return item

        normalized = dict(item)
        location_value = normalized.get("location")
        location_as_text = location_value if isinstance(location_value, str) else None

        detail = cls._coalesce(normalized.get("detail"), normalized.get("caption"))
        address = cls._coalesce(normalized.get("address"), location_as_text)
        image_url = cls._coalesce(
            normalized.get("imageUrl"), normalized.get("imageURL")
        )
        tags = cls._coalesce(normalized.get("tags"))
        info_link = cls._coalesce(
            normalized.get("infoLink"),
            cls._extract_info_link(normalized.get("infoLinkMarkdown")),
        )
        info_link_markdown = cls._format_info_link_markdown(info_link)

        normalized["detail"] = detail or ""
        normalized["address"] = address or ""
        normalized["imageUrl"] = image_url or ""
        normalized["tags"] = tags or ""
        normalized["infoLink"] = info_link or ""
        normalized["infoLinkMarkdown"] = info_link_markdown or ""
        return normalized

    async def __call__(self, state):
        """Call the presenter agent to generate and validate UI from restaurant data."""
        data = state["messages"][-1].content

        if self.use_ui:
            if self.a2ui_schema_object is None:
                logger.error(
                    "--- PresenterAgent: A2UI_SCHEMA is not loaded. Cannot perform UI validation. ---"
                )
                return {
                    "messages": state["messages"]
                    + [
                        self._build_ai_message(
                            build_text_output(
                                "I'm sorry, I'm facing an internal configuration error with my UI components."
                            ),
                            self.agent_name,
                            {
                                "model_id": "deterministic-a2ui-builder",
                                "total_tokens": 0,
                            },
                        )
                    ]
                }

            try:
                final_output = self._build_deterministic_ui_response(str(data))
                return {
                    "messages": state["messages"]
                    + [
                        self._build_ai_message(
                            final_output,
                            self.agent_name,
                            {
                                "model_id": "deterministic-a2ui-builder",
                                "total_tokens": 0,
                            },
                        )
                    ]
                }
            except Exception as exc:
                logger.exception(
                    "--- PresenterAgent: Deterministic UI build failed: %s ---", exc
                )
                return {
                    "messages": state["messages"]
                    + [
                        self._build_ai_message(
                            build_text_output(
                                "I'm sorry, I'm having trouble generating the interface for that request right now. "
                                "Please try again in a moment."
                            ),
                            self.agent_name,
                            {
                                "model_id": "deterministic-a2ui-builder",
                                "total_tokens": 0,
                            },
                        )
                    ]
                }

        try:
            response = await self._agent.ainvoke(
                {"messages": [HumanMessage(content=data)]}
            )
            final_response_content = self._coerce_text(response["messages"][-1].content)
            response_metadata = dict(
                getattr(response["messages"][-1], "response_metadata", {}) or {}
            )
            validated_response = response.copy()
            validated_response["messages"][-1] = self._build_ai_message(
                build_text_output(final_response_content),
                self.agent_name,
                response_metadata,
            )
            return validated_response
        except Exception as exc:
            logger.exception(
                "--- PresenterAgent: Text response generation failed: %s ---", exc
            )
            return {
                "messages": state["messages"]
                + [
                    self._build_ai_message(
                        build_text_output(
                            "I'm sorry, I'm having trouble generating the interface for that request right now. "
                            "Please try again in a moment."
                        ),
                        self.agent_name,
                    )
                ]
            }
