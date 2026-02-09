# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import httpx

import click
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, BasePushNotificationSender, InMemoryPushNotificationConfigStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2ui.a2ui_extension import get_a2ui_agent_extension
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse
from starlette.requests import Request
from agent.graph_executor import RestaurantGraphExecutor
from agent.graph.restaurant_graph import RestaurantGraph

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10002)
def main(host, port):
    try:
        capabilities = AgentCapabilities(
            streaming=True,
            push_notifications=True,
            extensions=[get_a2ui_agent_extension()],
        )
        skill = AgentSkill(
            id="find_restaurants",
            name="Find Restaurants Tool",
            description="Helps find restaurants based on user criteria (e.g., cuisine, location).",
            tags=["restaurant", "finder"],
            examples=["Find me the top 10 chinese restaurants in the US"],
        )

        base_url = f"http://{host}:{port}"

        #region Agent executor setup
        agent_base_url = f"{base_url}/agent"
        agent_card = AgentCard(
            name="Restaurant Agent",
            description="This agent helps find restaurants based on user criteria.",
            url=agent_base_url,
            version="1.0.0",
            default_input_modes=RestaurantGraph.SUPPORTED_CONTENT_TYPES,
            default_output_modes=RestaurantGraph.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        agent_executor = RestaurantGraphExecutor(base_url=agent_base_url)

        httpx_client = httpx.AsyncClient()
        agent_push_config_store = InMemoryPushNotificationConfigStore()
        agent_push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                        config_store=agent_push_config_store)
        agent_request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
            push_config_store=agent_push_config_store,
            push_sender=agent_push_sender
        )
        agent_server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=agent_request_handler
        )
        agent_app = agent_server.build()

        #region main app setup
        main_app = Starlette()

        main_app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://localhost:\d+",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        #region config endpoints
        async def get_config(request: Request):
            config = agent_executor.get_config()
            return JSONResponse(config)

        async def post_config(request: Request):
            try:
                data = await request.json()
                success, error = agent_executor.update_config(data)
                if success:
                    return JSONResponse({"status": "success", "message": "Configuration updated"})
                else:
                    return JSONResponse({"status": "error", "message": error}, status_code=400)
            except Exception as e:
                return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

        async def delete_config(request: Request):
            agent_executor.reset_config()
            return JSONResponse({"status": "success", "message": "Configuration reset to default"})

        #region app mount
        main_app.add_route("/agent/config", get_config, methods=["GET"])
        main_app.add_route("/agent/config", post_config, methods=["POST"])
        main_app.add_route("/agent/config", delete_config, methods=["DELETE"])

        main_app.mount("/static", StaticFiles(directory="images"), name="static")
        main_app.mount("/agent", agent_app)

        import uvicorn
        uvicorn.run(main_app, host=host, port=port)
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
