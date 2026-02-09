import json
import logging
import os
from langchain.tools import tool

logger = logging.getLogger(__name__)

@tool
def get_restaurants(cuisine: str, location: str, count: int = 5) -> str:
    """Call this tool to get a list of restaurants based on a cuisine and location.
    'count' is the number of restaurants to return.
    """
    logger.info(f"--- TOOL CALLED: get_restaurants (count: {count}) ---")
    logger.info(f"  - Cuisine: {cuisine}")
    logger.info(f"  - Location: {location}")

    items = []
    if "new york" in location.lower() or "ny" in location.lower():
        try:
            script_dir = os.path.dirname(__file__)
            file_path = os.path.join(script_dir, "restaurant_data.json")
            with open(file_path) as f:
                restaurant_data_str = f.read()
                # if base_url := tool_context.state.get("base_url"):                    
                #     restaurant_data_str = restaurant_data_str.replace("http://localhost:10002", base_url)
                #     logger.info(f'Updated base URL from tool context: {base_url}')
                all_items = json.loads(restaurant_data_str)        

            # Slice the list to return only the requested number of items
            items = all_items[:count]
            logger.info(
                f"  - Success: Found {len(all_items)} restaurants, returning {len(items)}."
            )

        except FileNotFoundError:
            logger.error(f"  - Error: restaurant_data.json not found at {file_path}")
        except json.JSONDecodeError:
            logger.error(f"  - Error: Failed to decode JSON from {file_path}")

    return json.dumps(items)

@tool
def get_weather(zipcode:int, date:str) -> dict[str,bool | int]:
    """ Gets the weather for a given city zipcode and date in format yyyy-mm-dd """
    
    # This is simple hardcoded data, could use zip code to fetch weather API and get real results
    city_weather = {
        "rain": True,
        "min_temperature": "50 f",
        "max_temperature": "62 f"
    }

    return city_weather