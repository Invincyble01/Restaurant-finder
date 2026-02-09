import os
from langchain.agents import create_agent
from langchain_oci import ChatOCIGenAI
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
load_dotenv()

from agent.graph.struct import AgentConfig

class RestaurantFinderAgent:
    """ Agent that has tools to find different restaurants depending on type of cuisine """

    AGENT_INSTRUCTIONS = """You are and agent that is specialized on finding different restaurants/caffeterias depending on type of cuisine.
    Return your answer in the best way possible so other LLM can read the information and proceed.
    Only return a list of the names of restaurants/caffeterias found."""

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
            self.agent_name = "food_place_agent"
            self.system_prompt = self.AGENT_INSTRUCTIONS
            self.tools_enabled = ["get_restaurants","get_cafes"]
        self._client = self._init_oci_client()
        self.agent = None

    async def initialize(self):
        self.agent = await self._build_agent()

    async def __call__(self, state):
        return await self.agent.ainvoke(state)

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
