#!/usr/bin/env python3
"""
Test script to check available MCP tools
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_mcp_adapters.client import MultiServerMCPClient
from src.config.config import MCP_SERVERS

async def test_mcp_tools():
    """Test available MCP tools"""
    print("🔍 Testing MCP Tools...")
    
    try:
        client = MultiServerMCPClient(MCP_SERVERS)
        tools = await client.get_tools()
        
        print(f"\n📋 Available Tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Check specifically for Opentrons tools
        opentrons_tools = [tool for tool in tools if 'opentrons' in tool.name.lower() or 'protocol' in tool.name.lower()]
        print(f"\n🤖 Opentrons-related Tools ({len(opentrons_tools)}):")
        for tool in opentrons_tools:
            print(f"  - {tool.name}: {tool.description}")
        
        return tools
        
    except Exception as e:
        print(f"❌ Error testing MCP tools: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
