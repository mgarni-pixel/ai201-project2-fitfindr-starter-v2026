"""Expose FitFindr's existing search implementation over stdio MCP.

Run ``python mcp_client.py`` to inspect the registered schema.
Only search moves across the boundary; outfit and caption tools stay local.
"""

from mcp.server.fastmcp import FastMCP

from tools import search_listings as _search_listings_impl

mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """Find thrift listings by keywords, optional size and inclusive USD price ceiling; return listing dictionaries or [] when none match."""
    return _search_listings_impl(description, size, max_price)


if __name__ == "__main__":
    mcp.run()
