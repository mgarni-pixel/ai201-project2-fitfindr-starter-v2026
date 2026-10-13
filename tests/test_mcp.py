"""Real stdio MCP checks. No model requests or transport doubles."""

import asyncio
import sys
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_client import MCPError, SERVER, call_tool
from tools import search_listings


class MCPTests(unittest.TestCase):
    def test_only_search_is_registered_with_inventory_schema(self):
        async def inspect():
            params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return (await session.list_tools()).tools
        offered = asyncio.run(inspect())
        self.assertEqual([tool.name for tool in offered], ["search_listings"])
        schema = offered[0].inputSchema
        self.assertEqual(schema["required"], ["description"])
        self.assertEqual(schema["properties"]["description"]["type"], "string")
        for name, kind in [("size", "string"), ("max_price", "number")]:
            self.assertIsNone(schema["properties"][name]["default"])
            self.assertEqual({s["type"] for s in schema["properties"][name]["anyOf"]},
                             {kind, "null"})

    def test_round_trip_preserves_positive_empty_and_filtered_results(self):
        for args in [
            {"description": "graphic tee"},
            {"description": "designer ballgown", "size": "XXS", "max_price": 5},
            {"description": "vintage", "size": None, "max_price": 20},
            {"description": "jeans", "size": "W30/L30", "max_price": 40},
        ]:
            with self.subTest(args=args):
                actual = call_tool("search_listings", args)
                self.assertIsInstance(actual, list)
                self.assertEqual(actual, search_listings(**args))

    def test_unknown_tool_is_an_explicit_error(self):
        with self.assertRaises(MCPError):
            call_tool("not_a_tool", {})


if __name__ == "__main__":
    unittest.main()
