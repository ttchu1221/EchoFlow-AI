from mcp.server.fastmcp import FastMCP
from bilibili_api import web_search

mcp = FastMCP()


@mcp.tool()
def general_search(keyword: str) -> dict:
    """Search Bilibili API with the given keyword.

    Args:
        keyword (str): Search term to look for on Bilibili.

    Returns:
        dict: Dictionary contains the search results from Bilibili,
              including a 'result' list with video entries.
    """
    return web_search(keyword)


if __name__ == "__main__":
    mcp.run(transport="stdio")
