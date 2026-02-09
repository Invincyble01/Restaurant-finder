import json
import logging
import os
from collections.abc import AsyncIterable
from typing import Any
from langchain.agents import create_agent
from langchain_oci import ChatOCIGenAI
from langchain.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
load_dotenv()

import jsonschema
from agent.prompt_builder import (
    A2UI_SCHEMA,
    RESTAURANT_UI_EXAMPLES,
    get_text_prompt,
    get_ui_prompt,
)
from agent.langchain_tools import get_restaurants

logger = logging.getLogger(__name__)

AGENT_INSTRUCTION = """
    You are a helpful restaurant finding assistant. Your goal is to help users find and book restaurants using a rich UI.

    To achieve this, you MUST follow this logic:

    1.  **For finding restaurants:**
        a. You MUST call the `get_restaurants` tool. Extract the cuisine, location, and a specific number (`count`) of restaurants from the user's query (e.g., for "top 5 chinese places", count is 5).
        b. After receiving the data, you MUST follow the instructions precisely to generate the final a2ui UI JSON, using the appropriate UI example from the `prompt_builder.py` based on the number of restaurants.

    2.  **For booking a table (when you receive a query like 'USER_WANTS_TO_BOOK...'):**
        a. You MUST use the appropriate UI example from `prompt_builder.py` to generate the UI, populating the `dataModelUpdate.contents` with the details from the user's query.

    3.  **For confirming a booking (when you receive a query like 'User submitted a booking...'):**
        a. You MUST use the appropriate UI example from `prompt_builder.py` to generate the confirmation UI, populating the `dataModelUpdate.contents` with the final booking details.
"""

class OCIRestaurantAgent:
    """ Agent using OCI libraries to find restaurants """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream"]

    def __init__(self, base_url: str, use_ui: bool = False):
        self.base_url = base_url
        self.use_ui = use_ui
        self._agent = self._build_agent(use_ui)
        self._user_id = "remote_agent"

        # --- MODIFICATION: Wrap the schema ---
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
        # --- END MODIFICATION ---

    def _build_agent(self, use_ui: bool) -> CompiledStateGraph:
        """Builds the LLM agent for the restaurant agent."""
        if use_ui:
            # Construct the full prompt with UI instructions, examples, and schema
            instruction = AGENT_INSTRUCTION + get_ui_prompt(
                self.base_url, RESTAURANT_UI_EXAMPLES
            )
        else:
            instruction = get_text_prompt()

        oci_llm = ChatOCIGenAI(
            model_id="openai.gpt-4.1",
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs={"temperature":0.7},
            auth_profile=os.getenv("AUTH_PROFILE"),
        )

        return create_agent(
            model=oci_llm,
            tools=[get_restaurants],
            system_prompt=instruction,
            name="restaurant_agent"
        )
    
    async def oci_stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        """ Function to call agent and stream responses """
        
        #TODO: Skipped session state flow, still working on why is required

        # --- Begin: UI Validation and Retry Logic ---
        max_retries = 1  # Total 2 attempts
        attempt = 0
        current_query_text = query

        # Ensure schema was loaded
        if self.use_ui and self.a2ui_schema_object is None:
            logger.error(
                "--- RestaurantAgent.stream: A2UI_SCHEMA is not loaded. "
                "Cannot perform UI validation. ---"
            )
            yield {
                "is_task_complete": True,
                "content": (
                    "I'm sorry, I'm facing an internal configuration error with my UI components. "
                    "Please contact support."
                ),
            }
            return
        
        while attempt <= max_retries:
            attempt += 1
            logger.info(
                f"--- RestaurantAgent.stream: Attempt {attempt}/{max_retries + 1} "
                f"for session {session_id} ---"
            )

            current_message = {"messages":[HumanMessage(query)]}
            config:RunnableConfig = {"run_id":str(session_id)}
            final_response_content = None
            final_model_state = None
            model_token_count = 0

            async for event in self._agent.astream(
                input=current_message,
                stream_mode="values",
                config=config
            ):
                latest_update:AnyMessage = event['messages'][-1]
                final_response_content = latest_update.content

                if hasattr(latest_update, 'tool_calls') and latest_update.tool_calls:
                    tool_name = str(latest_update.tool_calls[0].get('name'))
                    tool_args = str(latest_update.tool_calls[0].get('args'))
                    latest_update = f"Model calling tool: {tool_name} with args {tool_args}"
                elif isinstance(latest_update,ToolMessage):
                    tool_name = str(latest_update.name)
                    status_content = str(latest_update.content)
                    latest_update = f"Tool {tool_name} responded with:\n{status_content[:100]}...\n\nInformation passed to agent to build response"
                elif isinstance(latest_update, AIMessage):
                    status_content = str(latest_update.content)
                    model_id = str(latest_update.response_metadata.get("model_id"))
                    total_tokens_on_call = int(latest_update.response_metadata.get("total_tokens"))
                    model_token_count = model_token_count + total_tokens_on_call
                    agent_name = str(latest_update.name)
                    model_data = f"""
                        model_id: {model_id},
                        agent_name: {agent_name},
                        total_tokens_on_call: {str(model_token_count)}
                    """
                    latest_update = f"Agent current response:\n{status_content[:100]}...\n\nAgent metadata:\n{model_data}"
                    final_model_state = latest_update
                else:
                    status_content = str(latest_update.content)
                    latest_update = f"Processing task, current state:\n{status_content[:100]}..."

                # Yield intermediate updates on every attempt
                yield {
                    "is_task_complete": False,
                    "updates": latest_update
                }

            if final_response_content is None:
                logger.warning(
                    f"--- RestaurantAgent.stream: Received no final response content from runner "
                    f"(Attempt {attempt}). ---"
                )
                if attempt <= max_retries:
                    current_query_text = (
                        "I received no response. Please try again."
                        f"Please retry the original request: '{query}'"
                    )
                    continue  # Go to next retry
                else:
                    # Retries exhausted on no-response
                    final_response_content = "I'm sorry, I encountered an error and couldn't process your request."
                    # Fall through to send this as a text-only error
            
            is_valid = False
            error_message = ""

            if self.use_ui:
                logger.info(
                    f"--- RestaurantAgent.stream: Validating UI response (Attempt {attempt})... ---"
                )
                try:
                    if "---a2ui_JSON---" not in final_response_content:
                        raise ValueError("Delimiter '---a2ui_JSON---' not found.")

                    text_part, json_string = final_response_content.split(
                        "---a2ui_JSON---", 1
                    )

                    text_part = final_model_state

                    if not json_string.strip():
                        raise ValueError("JSON part is empty.")

                    json_string_cleaned = (
                        json_string.strip().lstrip("```json").rstrip("```").strip()
                    )

                    if not json_string_cleaned:
                        raise ValueError("Cleaned JSON string is empty.")

                    # --- New Validation Steps ---
                    # 1. Check if it's parsable JSON
                    parsed_json_data = json.loads(json_string_cleaned)

                    # 2. Check if it validates against the A2UI_SCHEMA
                    # This will raise jsonschema.exceptions.ValidationError if it fails
                    logger.info(
                        "--- RestaurantAgent.stream: Validating against A2UI_SCHEMA... ---"
                    )
                    jsonschema.validate(
                        instance=parsed_json_data, schema=self.a2ui_schema_object
                    )
                    # --- End New Validation Steps ---

                    logger.info(
                        f"--- RestaurantAgent.stream: UI JSON successfully parsed AND validated against schema. "
                        f"Validation OK (Attempt {attempt}). ---"
                    )
                    is_valid = True
                    final_response_content = f"{text_part}\n---a2ui_JSON---\n{json_string}"
                except (
                    ValueError,
                    json.JSONDecodeError,
                    jsonschema.exceptions.ValidationError,
                ) as e:
                    logger.warning(
                        f"--- RestaurantAgent.stream: A2UI validation failed: {e} (Attempt {attempt}) ---"
                    )
                    logger.warning(
                        f"--- Failed response content: {final_response_content[:500]}... ---"
                    )
                    error_message = f"Validation failed: {e}."

            else:  # Not using UI, so text is always "valid"
                is_valid = True

            if is_valid:
                logger.info(
                    f"--- RestaurantAgent.stream: Response is valid. Sending final response (Attempt {attempt}). ---"
                )
                # logger.info(f"Final response: {final_response_content}")
                yield {
                    "is_task_complete": True,
                    "content": final_response_content,
                }
                return  # We're done, exit the generator

            # --- If we're here, it means validation failed ---

            if attempt <= max_retries:
                logger.warning(
                    f"--- RestaurantAgent.stream: Retrying... ({attempt}/{max_retries + 1}) ---"
                )
                # Prepare the query for the retry
                current_query_text = (
                    f"Your previous response was invalid. {error_message} "
                    "You MUST generate a valid response that strictly follows the A2UI JSON SCHEMA. "
                    "The response MUST be a JSON list of A2UI messages. "
                    "Ensure the response is split by '---a2ui_JSON---' and the JSON part is well-formed. "
                    f"Please retry the original request: '{query}'"
                )
                # Loop continues...

            # --- If we're here, it means we've exhausted retries ---
            logger.error(
                "--- RestaurantAgent.stream: Max retries exhausted. Sending text-only error. ---"
            )
            yield {
                "is_task_complete": True,
                "content": (
                    "I'm sorry, I'm having trouble generating the interface for that request right now. "
                    "Please try again in a moment."
                ),
            }
            # --- End: UI Validation and Retry Logic ---

async def main():
    """ Test section for agent class """
    oci_agent = OCIRestaurantAgent("example",True)

    print("client started successfully ------------------------")

    async for response in oci_agent.oci_stream("Hello! Can you get me top 5 chinese restaurants in NY?",123):
        print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())