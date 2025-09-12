#!/usr/bin/env python3
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.config.config import MCP_SERVERS

async def test():
    client = MultiServerMCPClient(MCP_SERVERS)
    tools = await client.get_tools()
    print('Tool object type:', type(tools[0]) if tools else 'No tools')
    if tools:
        print('Tool methods:', [m for m in dir(tools[0]) if not m.startswith('_')])
        print('Tool name:', tools[0].name)
        print('Tool description:', tools[0].description)

if __name__ == "__main__":
    asyncio.run(test())
ve 