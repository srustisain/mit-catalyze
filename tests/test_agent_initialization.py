#!/usr/bin/env python3
import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.research_agent import ResearchAgent

async def test_agent_init():
    print("🧪 Testing Research Agent initialization...")
    
    try:
        agent = ResearchAgent()
        print("✅ Research Agent created")
        
        await agent.initialize()
        print("✅ Research Agent initialized")
        
        if agent.mcp_client:
            print("✅ MCP client available")
            tools = await agent.mcp_client.get_tools()
            print(f"✅ Found {len(tools)} tools in MCP client")
        else:
            print("❌ No MCP client")
            
        if agent.agent:
            print("✅ LangGraph agent created")
        else:
            print("❌ No LangGraph agent")
            
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_init())
