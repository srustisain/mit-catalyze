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

async def test_tool_calls():
    print("🧪 Testing MCP tool calls...")
    
    try:
        client = MultiServerMCPClient(MCP_SERVERS)
        tools = await client.get_tools()
        
        print(f"Found {len(tools)} tools available")
        
        # Test a simple ChEMBL tool call
        print("\n🔍 Testing ChEMBL search_compounds tool...")
        try:
            search_tool = next((tool for tool in tools if tool.name == "search_compounds"), None)
            if search_tool:
                result = await search_tool.ainvoke({"query": "aspirin", "limit": 3})
                print(f"✅ ChEMBL search result: {str(result)[:200]}...")
            else:
                print("❌ search_compounds tool not found")
        except Exception as e:
            print(f"❌ ChEMBL tool call failed: {e}")
        
        # Test a simple Opentrons tool call
        print("\n🔍 Testing Opentrons fetch_general tool...")
        try:
            general_tool = next((tool for tool in tools if tool.name == "fetch_general"), None)
            if general_tool:
                result = await general_tool.ainvoke({})
                print(f"✅ Opentrons general docs: {str(result)[:200]}...")
            else:
                print("❌ fetch_general tool not found")
        except Exception as e:
            print(f"❌ Opentrons tool call failed: {e}")
            
    except Exception as e:
        print(f"❌ MCP tool test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_calls())
