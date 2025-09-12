#!/usr/bin/env python3
"""
Test Intent Classification and Router System

Tests the intent classification system and smart router functionality.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.intent_classifier import IntentClassifier, IntentType
from src.agents.smart_router import SmartRouter
from src.clients.llm_client import LLMClient


async def test_intent_classification():
    """Test the intent classification system"""
    print("🧪 Testing Intent Classification System...")
    
    classifier = IntentClassifier()
    
    test_queries = [
        # Research queries
        ("What is the molecular weight of caffeine?", IntentType.RESEARCH),
        ("Explain the mechanism of PCR", IntentType.RESEARCH),
        ("Tell me about the structure of aspirin", IntentType.RESEARCH),
        ("How does DNA replication work?", IntentType.RESEARCH),
        
        # Protocol queries
        ("How do I synthesize aspirin?", IntentType.PROTOCOL),
        ("Create a protein extraction protocol", IntentType.PROTOCOL),
        ("What's the procedure for DNA isolation?", IntentType.PROTOCOL),
        ("Generate a step-by-step method for PCR", IntentType.PROTOCOL),
        
        # Automation queries
        ("Generate an Opentrons protocol for liquid handling", IntentType.AUTOMATE),
        ("Create a PyHamilton script for sample preparation", IntentType.AUTOMATE),
        ("Automate a 96-well plate filling process", IntentType.AUTOMATE),
        ("Make an OT-2 protocol for PCR setup", IntentType.AUTOMATE),
        
        # Safety queries
        ("Is this chemical combination safe?", IntentType.SAFETY),
        ("What PPE should I wear for this experiment?", IntentType.SAFETY),
        ("Check the safety data sheet for benzene", IntentType.SAFETY),
        ("What are the hazards of mixing these chemicals?", IntentType.SAFETY),
    ]
    
    correct_predictions = 0
    total_predictions = len(test_queries)
    
    for query, expected_intent in test_queries:
        print(f"\n📝 Query: {query}")
        print(f"🎯 Expected: {expected_intent.value}")
        
        try:
            result = await classifier.classify(query)
            predicted_intent = result.intent
            confidence = result.confidence
            
            print(f"🤖 Predicted: {predicted_intent.value} (confidence: {confidence:.2f})")
            print(f"🔍 Entities: {result.entities}")
            print(f"💭 Reasoning: {result.reasoning}")
            
            if predicted_intent == expected_intent:
                print("✅ CORRECT")
                correct_predictions += 1
            else:
                print("❌ INCORRECT")
            
        except Exception as e:
            print(f"💥 Error: {e}")
    
    accuracy = (correct_predictions / total_predictions) * 100
    print(f"\n📊 Classification Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
    
    return accuracy


async def test_smart_router():
    """Test the smart router system"""
    print("\n🧪 Testing Smart Router System...")
    
    router = SmartRouter()
    
    test_queries = [
        "What is the molecular weight of caffeine?",
        "How do I synthesize aspirin?",
        "Generate an Opentrons protocol for liquid handling",
        "Is this chemical combination safe?",
        "Explain the mechanism of PCR",
        "Create a protein extraction protocol",
        "Automate a 96-well plate filling process",
        "What PPE should I wear for this experiment?"
    ]
    
    successful_responses = 0
    total_queries = len(test_queries)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        
        try:
            result = await router.process_query(query)
            success = result.get("success", False)
            response = result.get("response", "No response")
            classification = result.get("classification")
            
            print(f"✅ Success: {success}")
            if classification:
                print(f"🎯 Classified as: {classification.intent.value} (confidence: {classification.confidence:.2f})")
            print(f"💬 Response: {response[:200]}...")
            
            if success:
                successful_responses += 1
            
        except Exception as e:
            print(f"💥 Error: {e}")
    
    success_rate = (successful_responses / total_queries) * 100
    print(f"\n📊 Router Success Rate: {success_rate:.1f}% ({successful_responses}/{total_queries})")
    
    return success_rate


async def test_edge_cases():
    """Test edge cases and ambiguous queries"""
    print("\n🧪 Testing Edge Cases...")
    
    classifier = IntentClassifier()
    router = SmartRouter()
    
    edge_cases = [
        "Hello, how are you?",  # Greeting
        "What's the weather like?",  # Non-chemistry
        "I need help with both synthesis and safety",  # Multi-intent
        "Can you help me?",  # Ambiguous
        "Show me the molecular structure and create a protocol",  # Multi-intent
        "",  # Empty query
        "asdfghjkl",  # Nonsense
    ]
    
    for query in edge_cases:
        print(f"\n📝 Edge Case: '{query}'")
        
        try:
            # Test classification
            classification = await classifier.classify(query)
            print(f"🎯 Classified as: {classification.intent.value} (confidence: {classification.confidence:.2f})")
            
            # Test router
            result = await router.process_query(query)
            success = result.get("success", False)
            print(f"✅ Router Success: {success}")
            
        except Exception as e:
            print(f"💥 Error: {e}")


async def main():
    """Run all tests"""
    print("🚀 Starting Intent Classification and Router Tests...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test intent classification
        classification_accuracy = await test_intent_classification()
        
        # Test smart router
        router_success_rate = await test_smart_router()
        
        # Test edge cases
        await test_edge_cases()
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print('='*60)
        print(f"Intent Classification Accuracy: {classification_accuracy:.1f}%")
        print(f"Router Success Rate: {router_success_rate:.1f}%")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎉 All tests completed!")
        
    except Exception as e:
        print(f"💥 Test suite failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
