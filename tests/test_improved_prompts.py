#!/usr/bin/env python3
"""
Test Improved Agent Prompts

Quick test to verify the improved, tighter agent prompts work correctly.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.smart_router import SmartRouter


async def test_improved_prompts():
    """Test the improved agent prompts"""
    print("🧪 Testing Improved Agent Prompts...")
    
    router = SmartRouter()
    
    # Test chemistry queries
    chemistry_queries = [
        "What is the molecular weight of caffeine?",
        "How do I synthesize aspirin?",
        "Generate an Opentrons protocol for liquid handling",
        "Is H2SO4 safe to handle?",
        "What is the structure of benzene?",
        "Create a protein extraction protocol",
        "What PPE should I wear for this experiment?",
        "Explain the mechanism of PCR"
    ]
    
    print(f"\n📊 Testing {len(chemistry_queries)} chemistry queries...")
    
    for i, query in enumerate(chemistry_queries, 1):
        print(f"\n--- Test {i} ---")
        print(f"Query: {query}")
        
        try:
            response = await router.process_query(query)
            print(f"Success: {response.get('success', False)}")
            print(f"Response: {response.get('response', 'No response')[:100]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test non-chemistry queries
    non_chemistry_queries = [
        "I have depression and need help",
        "What's the weather like today?",
        "How do I tell my brother I love him?",
        "What's a good recipe for pasta?",
        "Can you help me with my homework in math?"
    ]
    
    print(f"\n📊 Testing {len(non_chemistry_queries)} non-chemistry queries...")
    
    for i, query in enumerate(non_chemistry_queries, 1):
        print(f"\n--- Test {i} ---")
        print(f"Query: {query}")
        
        try:
            response = await router.process_query(query)
            print(f"Success: {response.get('success', False)}")
            print(f"Response: {response.get('response', 'No response')[:100]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n✅ Improved prompts test completed!")


if __name__ == "__main__":
    asyncio.run(test_improved_prompts())
