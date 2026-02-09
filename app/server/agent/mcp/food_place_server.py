from mcp.server.fastmcp import FastMCP

mcp = FastMCP("food_place_server", host="localhost",port=8000,stateless_http=True,mount_path="/mcp")

# This server is in charge of finding name places

@mcp.tool()
async def get_restaurants(cuisine_type: str, city:str) -> list[str]:
    """ Finds different restaurants depending on the city and type of cuisine selected. """

    chinese_restaurant_list = ["Xi'an Famous Foods","Han Dynasty","RedFarm","Mott 32", "Hwa Yuan Szechuan"]
    italian_restaurant_list = ["Lombardi's", "Di Fara", "Joe's Pizza", "L'Artusi", "Carbone"]

    if "chinese" in cuisine_type.lower():
        return chinese_restaurant_list
    elif "italian" in cuisine_type.lower():
        return italian_restaurant_list
    else:
        return [f"No restaurants found in {city}"]

@mcp.tool()
async def get_cafes(city:str) -> list[str]:
    """ Finds different cafes depending on the city selected """

    cafe_list = ["Marte", "Starbucks", "ItalianCoffe"]

    return cafe_list

if __name__ == "__main__":
    try:
        # Running server on http transport
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        print("Closing server")
    finally:
        print("Server closed")
