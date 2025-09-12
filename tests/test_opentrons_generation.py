#!/usr/bin/env python3
import asyncio
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.automate_agent import AutomateAgent

async def test_opentrons_generation():
    print("🧪 Testing Opentrons code generation...")
    
    # Initialize AutomateAgent
    automate_agent = AutomateAgent()
    await automate_agent.initialize()
    
    # Test query
    query = "write code for Opentrons to transfer 100µL from A1 to B1"
    
    print(f"\n📝 Testing query: '{query}'")
    print(f"🔍 Detected as Opentrons request: {automate_agent._is_opentrons_request(query)}")
    
    # Process the query
    result = await automate_agent.process_query(query)
    
    print(f"\n✅ Success: {result.get('success')}")
    print(f"🤖 Agent: {result.get('agent')}")
    print(f"📊 Used MCP: {result.get('used_mcp')}")
    
    if result.get('success'):
        response = result.get('response', '')
        print(f"\n📄 Response length: {len(response)} characters")
        print(f"\n📄 Response preview:")
        print(response)
        
        # Check if it contains actual Opentrons code
        if "```python" in response or "from opentrons" in response:
            print("\n✅ Contains actual Opentrons code!")
        else:
            print("\n❌ Does not contain actual Opentrons code")
    else:
        print(f"\n❌ Error: {result.get('error')}")
    
    print("\n🎉 Test complete!")

if __name__ == "__main__":
    asyncio.run(test_opentrons_generation())
