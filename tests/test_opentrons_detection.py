#!/usr/bin/env python3
import asyncio
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.automate_agent import AutomateAgent
from src.pipeline.mode_processor import ModeProcessor

async def test_opentrons_detection():
    print("🧪 Testing Opentrons detection and routing...")
    
    # Test AutomateAgent detection
    automate_agent = AutomateAgent()
    
    test_queries = [
        "write code for Opentrons",
        "generate Opentrons protocol",
        "create automation script for liquid handling",
        "I need a robot script",
        "how to use pipettes in lab automation",
        "what is Opentrons",  # Should NOT be detected as Opentrons request
        "explain chemical properties"  # Should NOT be detected as Opentrons request
    ]
    
    print("\n🔍 Testing AutomateAgent detection:")
    for query in test_queries:
        is_opentrons = automate_agent._is_opentrons_request(query)
        print(f"   '{query}' -> Opentrons: {is_opentrons}")
    
    # Test ModeProcessor detection
    mode_processor = ModeProcessor()
    
    print("\n🎯 Testing ModeProcessor routing:")
    for query in test_queries:
        suggested_mode = mode_processor.extract_mode_from_query(query)
        print(f"   '{query}' -> Mode: {suggested_mode}")
    
    print("\n✅ Detection tests complete!")

if __name__ == "__main__":
    asyncio.run(test_opentrons_detection())
