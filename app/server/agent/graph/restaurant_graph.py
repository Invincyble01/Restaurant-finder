from collections.abc import AsyncIterable
from typing import Any
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from agent.graph.apify_places_agent import ApifyPlacesAgent
from agent.graph.a2ui_builder import is_booking_request, is_booking_submission
from agent.graph.formatter_agent import FormatterAgent
from agent.graph.presenter_agent import PresenterAgent
from agent.graph.struct import AgentConfig, PresenterOutput, RestaurantGraphException

from dotenv import load_dotenv

load_dotenv()


class RestaurantGraph:
    """Graph to call the agent chain"""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream"]
    CONTENT_TRUNCATION_LENGTH = 50

    def __init__(
        self,
        base_url: str,
        use_ui: bool = False,
        graph_configuration: dict[str, AgentConfig] = None,
    ):
        if not graph_configuration:
            raise RestaurantGraphException()

        self._apify_places = ApifyPlacesAgent(graph_configuration["apify_places_agent"])
        self._formatter = FormatterAgent()
        self._presenter_agent = PresenterAgent(
            base_url, use_ui, graph_configuration["presenter_agent"]
        )

    async def build_graph(self):
        await self._apify_places.initialize()

        checkpointer = InMemorySaver()

        graph_builder = StateGraph(MessagesState)

        graph_builder.add_node("apify_places_agent", self._apify_places)
        graph_builder.add_node("formatter_agent", self._formatter)
        graph_builder.add_node("presenter_agent", self._presenter_agent)

        graph_builder.add_edge(START, "apify_places_agent")
        graph_builder.add_edge("apify_places_agent", "formatter_agent")
        graph_builder.add_edge("formatter_agent", "presenter_agent")
        graph_builder.add_edge("presenter_agent", END)

        self._restaurant_graph = graph_builder.compile(checkpointer=checkpointer)

    def _format_tool_call_message(self, message: AnyMessage) -> tuple[str, str]:
        tool_name = str(message.tool_calls[0].get("name"))
        tool_args = str(message.tool_calls[0].get("args"))
        agent_name = str(message.name) if message.name else ""
        timeline_message = f"{agent_name} called tool: {tool_name}"
        detailed_message = (
            f"Agent {agent_name} called tool: {tool_name} with args {tool_args}"
        )
        return timeline_message, detailed_message

    def _format_tool_message(self, message: ToolMessage) -> tuple[str, str]:
        tool_name = str(message.name)
        status_content = str(message.content)
        timeline_message = f"Tool {tool_name} responded"
        detailed_message = f"Tool {tool_name} responded with data:\n{status_content[: self.CONTENT_TRUNCATION_LENGTH]}"
        return timeline_message, detailed_message

    def _format_ai_message(
        self, message: AIMessage, model_token_count: int
    ) -> tuple[str, int, str]:
        status_content = str(message.content)
        model_id = str(message.response_metadata.get("model_id"))
        total_tokens_on_call = int(message.response_metadata.get("total_tokens", "0"))
        updated_token_count = model_token_count + total_tokens_on_call
        agent_name = str(message.name) if message.name else "GRAPH"
        model_data = f"""
            model_id: {model_id},
            total_tokens_on_call: {str(updated_token_count)}
        """
        formatted = f"{agent_name} response:\n{status_content[: self.CONTENT_TRUNCATION_LENGTH]}...\n\nAgent metadata:\n{model_data}"

        timeline_message = f"{agent_name} responded"
        detailed_message = formatted
        return timeline_message, updated_token_count, detailed_message

    def _format_human_message(
        self, message: HumanMessage, node_name: str
    ) -> tuple[str, str]:
        status_content = str(message.content)
        timeline_message = f"Current query: {node_name}"
        detailed_message = f"Query in process at {node_name}:\n{status_content[: self.CONTENT_TRUNCATION_LENGTH]}..."
        return timeline_message, detailed_message

    def _format_other_message(
        self, message: AnyMessage, node_name: str
    ) -> tuple[str, str]:
        status_content = str(message.content)
        timeline_message = f"Calling node: {node_name}"
        detailed_message = f"Calling node {node_name} with status: {status_content[: self.CONTENT_TRUNCATION_LENGTH]}"
        return timeline_message, detailed_message

    @staticmethod
    def _extract_final_output(message: AnyMessage) -> dict[str, Any]:
        if isinstance(message, AIMessage):
            presenter_output = getattr(message, "additional_kwargs", {}).get(
                "presenter_output"
            )
            if isinstance(presenter_output, dict):
                kind = str(presenter_output.get("kind") or "text")
                text = presenter_output.get("text")
                a2ui_messages = presenter_output.get("a2ui_messages")
                output = PresenterOutput(
                    kind=kind,
                    text=text if isinstance(text, str) else str(text or ""),
                    a2ui_messages=a2ui_messages
                    if isinstance(a2ui_messages, list)
                    else [],
                )
                return {
                    "kind": output.kind,
                    "text": output.text,
                    "a2ui_messages": output.a2ui_messages,
                }

        return {
            "kind": "text",
            "text": str(getattr(message, "content", "") or ""),
            "a2ui_messages": [],
        }

    @staticmethod
    def _is_presenter_only_query(query: str) -> bool:
        return is_booking_request(query) or is_booking_submission(query)

    async def _run_presenter_only(self, query: str, model_token_count: int):
        current_message = {"messages": [HumanMessage(query)]}
        yield {
            "is_task_complete": False,
            "updates": "Current query: presenter_agent",
            "detailed_updates": f"Query in process at presenter_agent:\n{query[: self.CONTENT_TRUNCATION_LENGTH]}...",
        }

        response = await self._presenter_agent(current_message)
        latest_message: AnyMessage = response["messages"][-1]
        timeline_message, model_token_count, detailed_message = self._format_ai_message(
            latest_message, model_token_count
        )

        yield {
            "is_task_complete": False,
            "updates": timeline_message,
            "detailed_updates": detailed_message,
        }

        yield {
            "is_task_complete": True,
            "final_output": self._extract_final_output(latest_message),
            "detailed_updates": detailed_message,
            "token_count": str(model_token_count),
        }

    async def call_restaurant_graph(
        self, query, session_id
    ) -> AsyncIterable[dict[str, Any]]:
        if self._is_presenter_only_query(query):
            async for event in self._run_presenter_only(query, 0):
                yield event
            return

        current_message = {"messages": [HumanMessage(query)]}
        config: RunnableConfig = {
            "run_id": str(session_id),
            "configurable": {"thread_id": str(session_id)},
        }
        final_output = None
        model_token_count = 0
        node_name = "START"

        # Stream graph execution
        async for chunk in self._restaurant_graph.astream(
            input=current_message, config=config, stream_mode="values", subgraphs=True
        ):
            latest_message: AnyMessage = chunk[1]["messages"][-1]
            final_output = self._extract_final_output(latest_message)

            # Format the message based on its type
            if hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
                timeline_message, detailed_message = self._format_tool_call_message(
                    latest_message
                )
            elif isinstance(latest_message, ToolMessage):
                timeline_message, detailed_message = self._format_tool_message(
                    latest_message
                )
            elif isinstance(latest_message, AIMessage):
                timeline_message, model_token_count, detailed_message = (
                    self._format_ai_message(latest_message, model_token_count)
                )
            elif isinstance(latest_message, HumanMessage):
                # For human messages, update node_name from state before formatting
                state = self._restaurant_graph.get_state(config=config, subgraphs=True)
                node_name = str(state.next[0]) if state.next else "GRAPH"
                timeline_message, detailed_message = self._format_human_message(
                    latest_message, node_name
                )
            else:
                timeline_message, detailed_message = self._format_other_message(
                    latest_message, node_name
                )

            # Update node_name from graph state for non-human messages
            if not isinstance(latest_message, HumanMessage):
                state = self._restaurant_graph.get_state(config=config, subgraphs=True)
                node_name = str(state.next[0]) if state.next else "GRAPH"

            # Yield intermediate updates
            yield {
                "is_task_complete": False,
                "updates": timeline_message,
                "detailed_updates": detailed_message,
            }

        yield {
            "is_task_complete": True,
            "final_output": final_output,
            "detailed_updates": detailed_message,
            "token_count": str(model_token_count),
        }


# region Testing
async def main():
    graph = RestaurantGraph(base_url="localhost", use_ui=True)

    await graph.build_graph()

    async for event in graph.call_restaurant_graph(
        "Top 5 chinese restaurants in Ny?", "1234"
    ):
        if event["is_task_complete"]:
            print(f"\nFinal event: {event}")
        else:
            if len(event["updates"]) < 200:
                print(event)
            else:
                print(event["updates"][:200])


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
