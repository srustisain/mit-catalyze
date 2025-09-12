#!/usr/bin/env python3
import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_mcp_adapters.client import MultiServerMCPClient

# MCP server configuration
MCP_SERVERS = {
    "chembl": {
        "transport": "stdio",
        "command": "node",
        "args": ["mcp_servers/chembl-mcp-server/build/index.js"]
    },
    
    "opentrons": {
        "transport": "stdio",
        "command": "node",
        "args": ["mcp_servers/opentrons-mcp-server/dist/index.js"]
    }
}

async def test_mcp_servers():
    print("🧪 Testing MCP servers...")
    
    try:
        # Test individual servers first
        for server_name, server_config in MCP_SERVERS.items():
            print(f"\n🔍 Testing {server_name} server...")
            try:
                client = MultiServerMCPClient({server_name: server_config})
                tools = await client.get_tools()
                print(f"✅ {server_name}: Found {len(tools)} tools")
                for tool in tools:
                    print(f"   - {tool.name}: {tool.description[:100]}...")
            except Exception as e:
                print(f"❌ {server_name}: Error - {e}")
        
        # Test combined client
        print(f"\n🔍 Testing combined MCP client...")
        try:
            client = MultiServerMCPClient(MCP_SERVERS)
            tools = await client.get_tools()
            print(f"✅ Combined: Found {len(tools)} tools total")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description[:100]}...")
        except Exception as e:
            print(f"❌ Combined client: Error - {e}")
            
    except Exception as e:
        print(f"❌ MCP test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_servers())
