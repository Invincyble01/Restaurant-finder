import os
from langchain.agents import create_agent
from langchain_oci import ChatOCIGenAI
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
load_dotenv()

from agent.graph.struct import AgentConfig

class DataAgent:
    """ Agent in charge of finding the data about the restaurants specified to the user """

    AGENT_INSTRUCTIONS = """You are an agent expert in finding restaurant data.
    You will receive the information about a list of restaurants or caffeterias to find information about.
    Your job is to gather that information and pass the full data to a new agent that will respond to the user.
    Important, consider including links, image references and other UI data to be rendered during next steps.
    Consider that caffeteria or restaurant data should be complete, use tools as required according to context.
    Make sure to use the exact restaurant names from information."""

    def __init__(self, config: AgentConfig = None):
        if config:
            self.oci_model = config.model
            self.agent_name = config.name
            self.model_temperature = config.temperature
            self.system_prompt = config.system_prompt if config.system_prompt else self.AGENT_INSTRUCTIONS
            self.tools_enabled = config.tools_enabled
        else:
            self.oci_model = "xai.grok-4-fast-non-reasoning"
            self.model_temperature = 0.7
            self.agent_name = "place_data_agent"
            self.system_prompt = self.AGENT_INSTRUCTIONS
            self.tools_enabled = ["get_cafe_data","get_restaurant_data"]
        self._client = self._init_oci_client()
        self.agent = None

    async def initialize(self):
        self.agent = await self._build_agent()

    async def __call__(self, state):
        # Message cleanup
        user_query = str(state['messages'][0].content)
        last_model_response = str(state['messages'][-1])
        messages = {
            'messages':[
                HumanMessage(user_query),
                last_model_response
            ]
        }
        return await self.agent.ainvoke(messages)

    def _init_oci_client(self):
        client = ChatOCIGenAI(
            model_id=self.oci_model,
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs={"temperature": self.model_temperature},
            auth_profile=os.getenv("AUTH_PROFILE"),
        )

        # client = ChatOpenAI(
        #     base_url=os.getenv("OPENAI_ENDPOINT"),
        #     api_key=os.getenv("OPENAI_KEY"),
        #     model="openai.gpt-4.1",
        #     store = False,
        # )

        return client

    async def _build_agent(self):
        tools = await self._get_mcp_tools()

        # filters the tools selected by user
        agent_tools = [tool for tool in tools if tool.name in self.tools_enabled]

        return create_agent(
            model=self._client,
            tools=agent_tools,
            system_prompt=self.system_prompt,
            name=self.agent_name
        )

    async def _get_mcp_tools(self):
        # MCP client connection using langchain mcp
        client = MultiServerMCPClient(
            {
                "data_server": {
                    "transport": "streamable_http",  # HTTP-based remote server
                    "url": "http://localhost:8001/mcp",
                },
                "food_place_server": {
                    "transport": "streamable_http",  # HTTP-based remote server
                    "url": "http://localhost:8000/mcp",
                }
            }
        )

        return await client.get_tools()

# region testing
async def main():
    agent = DataAgent()
    await agent.initialize()

    messages = {'messages': [HumanMessage(content='Can you give me top 3 chinese restaurants in NY?', additional_kwargs={}, response_metadata={}), AIMessage(content="Xi'an Famous Foods\nHan Dynasty\nRedFarm", additional_kwargs={}, response_metadata={}, tool_calls=[], invalid_tool_calls=[])]}

    async for chunk in agent.agent.astream(
            input=messages,
            stream_mode='values'
    ):
        print(chunk['messages'][-1])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
