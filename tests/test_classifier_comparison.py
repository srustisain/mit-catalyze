#!/usr/bin/env python3
"""
Classifier Comparison Test

Compares rule-based + LLM hybrid vs LangChain built-in tools for intent classification.
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.intent_classifier import IntentClassifier as RuleBasedClassifier
from src.agents.langchain_classifier import LangChainIntentClassifier
from src.clients.llm_client import LLMClient


async def compare_classifiers():
    """Compare rule-based vs LangChain classifiers"""
    print("🔬 Comparing Intent Classification Approaches...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize classifiers
    llm_client = LLMClient()
    rule_based = RuleBasedClassifier(llm_client)
    langchain_based = LangChainIntentClassifier(llm_client)
    
    test_queries = [
        "What is the molecular weight of caffeine?",
        "How do I synthesize aspirin?",
        "Generate an Opentrons protocol for liquid handling",
        "Is this chemical combination safe?",
        "Explain the mechanism of PCR",
        "Create a protein extraction protocol",
        "Automate a 96-well plate filling process",
        "What PPE should I wear for this experiment?",
        "Tell me about the structure of benzene",
        "Make a step-by-step method for DNA isolation"
    ]
    
    print(f"\n📊 Testing {len(test_queries)} queries...")
    
    # Test rule-based classifier
    print("\n🔧 Testing Rule-Based + LLM Hybrid Classifier...")
    rule_based_results = []
    rule_based_times = []
    
    for query in test_queries:
        start_time = time.time()
        try:
            result = await rule_based.classify(query)
            end_time = time.time()
            
            rule_based_results.append(result)
            rule_based_times.append(end_time - start_time)
            
            print(f"  ✅ {query[:50]}... -> {result.intent.value} ({result.confidence:.2f})")
        except Exception as e:
            print(f"  ❌ {query[:50]}... -> Error: {e}")
            rule_based_times.append(0)
    
    # Test LangChain classifier
    print("\n🤖 Testing LangChain Built-in Classifier...")
    langchain_results = []
    langchain_times = []
    
    for query in test_queries:
        start_time = time.time()
        try:
            result = await langchain_based.classify(query)
            end_time = time.time()
            
            langchain_results.append(result)
            langchain_times.append(end_time - start_time)
            
            print(f"  ✅ {query[:50]}... -> {result.intent} ({result.confidence:.2f})")
        except Exception as e:
            print(f"  ❌ {query[:50]}... -> Error: {e}")
            langchain_times.append(0)
    
    # Compare results
    print(f"\n{'='*80}")
    print("📊 COMPARISON RESULTS")
    print('='*80)
    
    # Accuracy comparison
    rule_based_accuracy = sum(1 for r in rule_based_results if r.intent.value != "unknown") / len(rule_based_results)
    langchain_accuracy = sum(1 for r in langchain_results if r.intent != "unknown") / len(langchain_results)
    
    print(f"Rule-Based Accuracy: {rule_based_accuracy:.1%}")
    print(f"LangChain Accuracy: {langchain_accuracy:.1%}")
    
    # Speed comparison
    rule_based_avg_time = sum(rule_based_times) / len(rule_based_times)
    langchain_avg_time = sum(langchain_times) / len(langchain_times)
    
    print(f"\nRule-Based Avg Time: {rule_based_avg_time:.3f}s")
    print(f"LangChain Avg Time: {langchain_avg_time:.3f}s")
    print(f"Speed Improvement: {rule_based_avg_time/langchain_avg_time:.1f}x")
    
    # Confidence comparison
    rule_based_avg_confidence = sum(r.confidence for r in rule_based_results) / len(rule_based_results)
    langchain_avg_confidence = sum(r.confidence for r in langchain_results) / len(langchain_results)
    
    print(f"\nRule-Based Avg Confidence: {rule_based_avg_confidence:.2f}")
    print(f"LangChain Avg Confidence: {langchain_avg_confidence:.2f}")
    
    # Entity extraction comparison
    rule_based_avg_entities = sum(len(r.entities) for r in rule_based_results) / len(rule_based_results)
    langchain_avg_entities = sum(len(r.entities) for r in langchain_results) / len(langchain_results)
    
    print(f"\nRule-Based Avg Entities: {rule_based_avg_entities:.1f}")
    print(f"LangChain Avg Entities: {langchain_avg_entities:.1f}")
    
    # Detailed comparison
    print(f"\n{'='*80}")
    print("🔍 DETAILED COMPARISON")
    print('='*80)
    
    for i, query in enumerate(test_queries):
        print(f"\nQuery {i+1}: {query}")
        print(f"Rule-Based: {rule_based_results[i].intent.value} ({rule_based_results[i].confidence:.2f}) - {rule_based_times[i]:.3f}s")
        print(f"LangChain:  {langchain_results[i].intent} ({langchain_results[i].confidence:.2f}) - {langchain_times[i]:.3f}s")
        
        # Check if they agree
        rule_intent = rule_based_results[i].intent.value
        langchain_intent = langchain_results[i].intent
        if rule_intent == langchain_intent:
            print("  ✅ AGREEMENT")
        else:
            print("  ❌ DISAGREEMENT")
    
    # Recommendations
    print(f"\n{'='*80}")
    print("💡 RECOMMENDATIONS")
    print('='*80)
    
    if langchain_accuracy > rule_based_accuracy:
        print("✅ LangChain classifier has higher accuracy")
    else:
        print("✅ Rule-based classifier has higher accuracy")
    
    if langchain_avg_time < rule_based_avg_time:
        print("✅ LangChain classifier is faster")
    else:
        print("✅ Rule-based classifier is faster")
    
    if langchain_avg_confidence > rule_based_avg_confidence:
        print("✅ LangChain classifier has higher confidence")
    else:
        print("✅ Rule-based classifier has higher confidence")
    
    print(f"\n🎯 Overall Winner: {'LangChain' if langchain_accuracy > rule_based_accuracy else 'Rule-Based'}")
    
    return {
        "rule_based": {
            "accuracy": rule_based_accuracy,
            "avg_time": rule_based_avg_time,
            "avg_confidence": rule_based_avg_confidence,
            "avg_entities": rule_based_avg_entities
        },
        "langchain": {
            "accuracy": langchain_accuracy,
            "avg_time": langchain_avg_time,
            "avg_confidence": langchain_avg_confidence,
            "avg_entities": langchain_avg_entities
        }
    }


async def test_langchain_features():
    """Test specific LangChain features"""
    print("\n🧪 Testing LangChain Specific Features...")
    
    classifier = LangChainIntentClassifier()
    
    # Test batch processing
    queries = [
        "What is caffeine?",
        "How to make aspirin?",
        "Generate Opentrons protocol"
    ]
    
    print("Testing batch processing...")
    start_time = time.time()
    results = await classifier.classify_batch(queries)
    end_time = time.time()
    
    print(f"Batch processed {len(queries)} queries in {end_time - start_time:.3f}s")
    for i, result in enumerate(results):
        print(f"  {queries[i]}: {result.intent} ({result.confidence:.2f})")
    
    # Test classifier stats
    stats = await classifier.get_classification_stats()
    print(f"\nClassifier Stats: {stats}")


async def main():
    """Run the comparison test"""
    try:
        # Run comparison
        comparison_results = await compare_classifiers()
        
        # Test LangChain features
        await test_langchain_features()
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎉 Comparison test completed!")
        
    except Exception as e:
        print(f"💥 Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
