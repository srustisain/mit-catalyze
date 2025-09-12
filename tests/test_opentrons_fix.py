#!/usr/bin/env python3
import asyncio
from src.clients.opentrons_validator import OpentronsCodeGenerator, OpentronsValidator
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.config.config import MCP_SERVERS

async def test():
    print("🧪 Testing Opentrons MCP tool calls...")
    
    try:
        # Initialize MCP client
        mcp_client = MultiServerMCPClient(MCP_SERVERS)
        
        # Initialize Opentrons generator
        validator = OpentronsValidator()
        generator = OpentronsCodeGenerator(validator=validator, mcp_client=mcp_client)
        
        # Test getting Opentrons documentation
        print("Testing Opentrons documentation retrieval...")
        docs = await generator._get_opentrons_documentation("Create a simple protocol")
        print(f"Documentation result: {docs[:200]}...")
        
        print("✅ Opentrons MCP tool calls working!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
