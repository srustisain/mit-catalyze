#!/usr/bin/env python3
"""
Test PCR protocol generation fix
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.automate_agent import AutomateAgent

async def test_pcr_protocol():
    """Test PCR protocol generation"""
    print("🧪 Testing PCR Protocol Generation...")
    
    try:
        agent = AutomateAgent()
        result = await agent._process_opentrons_request('Create a Flex protocol for PCR setup with 96-well plate', {})
        
        print(f"Success: {result['success']}")
        print(f"Response length: {len(result.get('response', ''))}")
        
        if result.get('opentrons_code'):
            print(f"Code length: {len(result['opentrons_code'])}")
            print("\nGenerated Code:")
            print("="*50)
            print(result['opentrons_code'])
            print("="*50)
        
        if not result['success']:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_pcr_protocol())
