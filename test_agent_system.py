#!/usr/bin/env python3
"""
Test script for the new agent system
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import PipelineManager
from src.agents import RouterAgent, ResearchAgent, ProtocolAgent, AutomateAgent, SafetyAgent


async def test_agents():
    """Test all agents individually"""
    print("🧪 Testing Catalyze Agent System")
    print("=" * 50)
    
    # Test Router Agent
    print("\n🔀 Testing Router Agent...")
    router = RouterAgent()
    try:
        result = await router.process_query("What is the molecular weight of caffeine?")
        print(f"✅ Router Agent: {result.get('success', False)}")
        if result.get('routing_decision'):
            print(f"   Suggested agent: {result['routing_decision'].get('agent', 'unknown')}")
    except Exception as e:
        print(f"❌ Router Agent failed: {e}")
    
    # Test Research Agent
    print("\n🔬 Testing Research Agent...")
    research = ResearchAgent()
    try:
        result = await research.process_query("What is the molecular weight of caffeine?")
        print(f"✅ Research Agent: {result.get('success', False)}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
        print(f"   Used MCP: {result.get('used_mcp', False)}")
    except Exception as e:
        print(f"❌ Research Agent failed: {e}")
    
    # Test Protocol Agent
    print("\n📋 Testing Protocol Agent...")
    protocol = ProtocolAgent()
    try:
        result = await protocol.process_query("Generate a protocol for synthesizing aspirin")
        print(f"✅ Protocol Agent: {result.get('success', False)}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
    except Exception as e:
        print(f"❌ Protocol Agent failed: {e}")
    
    # Test Automate Agent
    print("\n🤖 Testing Automate Agent...")
    automate = AutomateAgent()
    try:
        result = await automate.process_query("Create an automation script for liquid handling")
        print(f"✅ Automate Agent: {result.get('success', False)}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
    except Exception as e:
        print(f"❌ Automate Agent failed: {e}")
    
    # Test Safety Agent
    print("\n🛡️ Testing Safety Agent...")
    safety = SafetyAgent()
    try:
        result = await safety.process_query("What are the safety hazards of sulfuric acid?")
        print(f"✅ Safety Agent: {result.get('success', False)}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
    except Exception as e:
        print(f"❌ Safety Agent failed: {e}")
    
    # Test Pipeline Manager
    print("\n🚀 Testing Pipeline Manager...")
    pipeline = PipelineManager()
    try:
        await pipeline.initialize()
        print("✅ Pipeline Manager initialized")
        
        # Test different modes
        modes = ["research", "protocol", "automate", "safety"]
        for mode in modes:
            result = await pipeline.process_query(
                f"Test query for {mode} mode", 
                mode=mode
            )
            print(f"   {mode.capitalize()} mode: {result.get('success', False)}")
            
    except Exception as e:
        print(f"❌ Pipeline Manager failed: {e}")
    
    print("\n🎯 Agent System Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_agents())
