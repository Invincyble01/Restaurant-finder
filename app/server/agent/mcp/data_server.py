import json
import os
from mcp.server.fastmcp import FastMCP

from typing import List

mcp = FastMCP("data_server", host="localhost",port=8001,stateless_http=True,mount_path="/mcp")

def load_restaurant_json():
    # Load data from JSON files
    script_dir = os.path.dirname(__file__)
    with open(os.path.join(script_dir, 'chinese_data.json'), 'r') as f:
        chinese_data = json.load(f)

    with open(os.path.join(script_dir, 'italian_data.json'), 'r') as f:
        italian_data = json.load(f)

    all_restaurants = chinese_data + italian_data

    return all_restaurants

def load_caffeteria_json():
    script_dir = os.path.dirname(__file__)
    with open(os.path.join(script_dir, 'caffeteria_data.json'), 'r') as f:
        cafeteria_data = json.load(f)

    return cafeteria_data

# this server is in charge of finding information about the restaurants selected

@mcp.tool()
async def get_restaurant_data(restaurant_names: str) -> str:
    """ Uses the restaurant names to return data for the specified restaurants. """

    all_restaurants = load_restaurant_json()

    matching_items = [item for item in all_restaurants if item['name'] in restaurant_names]
    return json.dumps(matching_items)

@mcp.tool()
async def get_cafe_data(cafe_names: str) -> str:
    """ Returns information about the specified cafes based on names """

    cafeteria_data = load_caffeteria_json()

    matching_items = [item for item in cafeteria_data if item['name'] in cafe_names]
    return json.dumps(matching_items)

if __name__ == "__main__":
    try:
        # Running server on http transport
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        print("Closing server")
    finally:
        print("Server closed")
