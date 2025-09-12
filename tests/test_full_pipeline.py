#!/usr/bin/env python3
import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import PipelineManager

async def test_full_pipeline():
    print("🧪 Testing Full Pipeline with MCP Tools...")
    
    try:
        # Initialize pipeline manager
        pipeline_manager = PipelineManager()
        await pipeline_manager.initialize()
        print("✅ Pipeline initialized")
        
        # Test research query
        print("\n🔬 Testing research query...")
        result = await pipeline_manager.process_query(
            "What is the molecular weight of aspirin and how can I synthesize it?",
            mode="research"
        )
        
        print(f"✅ Research result: {result.get('success', False)}")
        print(f"   Agent used: {result.get('agent', 'unknown')}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
        print(f"   Used MCP tools: {result.get('used_mcp', False)}")
        
        # Test protocol query
        print("\n📋 Testing protocol query...")
        result = await pipeline_manager.process_query(
            "Generate a protocol for synthesizing aspirin from salicylic acid",
            mode="protocol"
        )
        
        print(f"✅ Protocol result: {result.get('success', False)}")
        print(f"   Agent used: {result.get('agent', 'unknown')}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
        print(f"   Used MCP tools: {result.get('used_mcp', False)}")
        
        # Test automation query
        print("\n🤖 Testing automation query...")
        result = await pipeline_manager.process_query(
            "Create an Opentrons protocol for a PCR reaction",
            mode="automate"
        )
        
        print(f"✅ Automation result: {result.get('success', False)}")
        print(f"   Agent used: {result.get('agent', 'unknown')}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
        print(f"   Used MCP tools: {result.get('used_mcp', False)}")
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
