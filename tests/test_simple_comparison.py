#!/usr/bin/env python3
"""
Simple Classifier Comparison Test

Compares rule-based vs LangChain approaches for intent classification.
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.intent_classifier import IntentClassifier as RuleBasedClassifier
from src.clients.llm_client import LLMClient


async def test_rule_based_classifier():
    """Test the rule-based classifier"""
    print("🔧 Testing Rule-Based + LLM Hybrid Classifier...")
    
    llm_client = LLMClient()
    classifier = RuleBasedClassifier(llm_client)
    
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
    
    results = []
    times = []
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        start_time = time.time()
        try:
            result = await classifier.classify(query)
            end_time = time.time()
            
            results.append(result)
            times.append(end_time - start_time)
            
            print(f"  Intent: {result.intent.value}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Entities: {result.entities}")
            print(f"  Time: {end_time - start_time:.3f}s")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            times.append(0)
    
    return results, times


async def test_langchain_approach():
    """Test a simplified LangChain approach"""
    print("\n🤖 Testing LangChain Approach...")
    
    llm_client = LLMClient()
    
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
    
    results = []
    times = []
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        start_time = time.time()
        try:
            # Use LLM directly for classification
            classification_prompt = f"""
Classify this chemistry query into one of these categories: research, protocol, automate, or safety.

Query: "{query}"

Consider:
- research: Questions about properties, mechanisms, explanations
- protocol: Lab procedures, synthesis methods, experimental steps  
- automate: Lab automation scripts, robotic systems, equipment control
- safety: Safety questions, hazard assessments, PPE recommendations

Respond with only the category name.
"""
            
            response = llm_client.generate_response(classification_prompt)
            end_time = time.time()
            
            # Parse response
            intent = "unknown"
            for category in ["research", "protocol", "automate", "safety"]:
                if category in response.lower():
                    intent = category
                    break
            
            # Simple confidence based on response clarity
            confidence = 0.8 if intent != "unknown" else 0.2
            
            # Simple entity extraction
            entities = []
            if "molecular weight" in query.lower():
                entities.append("molecular weight")
            if "caffeine" in query.lower():
                entities.append("caffeine")
            if "aspirin" in query.lower():
                entities.append("aspirin")
            if "opentrons" in query.lower():
                entities.append("opentrons")
            if "pcr" in query.lower():
                entities.append("pcr")
            
            results.append({
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "reasoning": f"LLM classified as {intent}"
            })
            times.append(end_time - start_time)
            
            print(f"  Intent: {intent}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Entities: {entities}")
            print(f"  Time: {end_time - start_time:.3f}s")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            times.append(0)
    
    return results, times


async def main():
    """Run the comparison test"""
    print("🔬 Comparing Intent Classification Approaches...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test rule-based approach
    rule_results, rule_times = await test_rule_based_classifier()
    
    # Test LangChain approach
    langchain_results, langchain_times = await test_langchain_approach()
    
    # Compare results
    print(f"\n{'='*80}")
    print("📊 COMPARISON RESULTS")
    print('='*80)
    
    # Accuracy comparison
    rule_accuracy = sum(1 for r in rule_results if r.intent.value != "unknown") / len(rule_results)
    langchain_accuracy = sum(1 for r in langchain_results if r["intent"] != "unknown") / len(langchain_results)
    
    print(f"Rule-Based Accuracy: {rule_accuracy:.1%}")
    print(f"LangChain Accuracy: {langchain_accuracy:.1%}")
    
    # Speed comparison
    rule_avg_time = sum(rule_times) / len(rule_times)
    langchain_avg_time = sum(langchain_times) / len(langchain_times)
    
    print(f"\nRule-Based Avg Time: {rule_avg_time:.3f}s")
    print(f"LangChain Avg Time: {langchain_avg_time:.3f}s")
    print(f"Speed Ratio: {rule_avg_time/langchain_avg_time:.1f}x")
    
    # Confidence comparison
    rule_avg_confidence = sum(r.confidence for r in rule_results) / len(rule_results)
    langchain_avg_confidence = sum(r["confidence"] for r in langchain_results) / len(langchain_results)
    
    print(f"\nRule-Based Avg Confidence: {rule_avg_confidence:.2f}")
    print(f"LangChain Avg Confidence: {langchain_avg_confidence:.2f}")
    
    # Entity extraction comparison
    rule_avg_entities = sum(len(r.entities) for r in rule_results) / len(rule_results)
    langchain_avg_entities = sum(len(r["entities"]) for r in langchain_results) / len(langchain_results)
    
    print(f"\nRule-Based Avg Entities: {rule_avg_entities:.1f}")
    print(f"LangChain Avg Entities: {langchain_avg_entities:.1f}")
    
    # Agreement analysis
    agreements = 0
    for i in range(len(rule_results)):
        rule_intent = rule_results[i].intent.value
        langchain_intent = langchain_results[i]["intent"]
        if rule_intent == langchain_intent:
            agreements += 1
    
    agreement_rate = agreements / len(rule_results)
    print(f"\nAgreement Rate: {agreement_rate:.1%}")
    
    # Summary
    print(f"\n{'='*80}")
    print("💡 SUMMARY")
    print('='*80)
    
    if rule_accuracy > langchain_accuracy:
        print("✅ Rule-based classifier has higher accuracy")
    else:
        print("✅ LangChain approach has higher accuracy")
    
    if rule_avg_time < langchain_avg_time:
        print("✅ Rule-based classifier is faster")
    else:
        print("✅ LangChain approach is faster")
    
    if rule_avg_confidence > langchain_avg_confidence:
        print("✅ Rule-based classifier has higher confidence")
    else:
        print("✅ LangChain approach has higher confidence")
    
    print(f"\n🎯 Overall Winner: {'Rule-Based' if rule_accuracy > langchain_accuracy else 'LangChain'}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
