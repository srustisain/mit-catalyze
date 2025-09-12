"""
Intent Classification System

Classifies user queries into one of four categories:
- research: Chemistry research questions, explanations, compound lookups
- protocol: Lab protocol generation, experimental procedures
- automate: Lab automation scripts, Opentrons protocols, robotic systems
- safety: Safety analysis, hazard assessment, PPE recommendations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
import json

from src.clients.llm_client import LLMClient


class IntentType(Enum):
    RESEARCH = "research"
    PROTOCOL = "protocol"
    AUTOMATE = "automate"
    SAFETY = "safety"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of intent classification"""
    intent: IntentType
    confidence: float
    entities: List[str]
    reasoning: str
    secondary_intents: List[Tuple[IntentType, float]] = None


class IntentClassifier:
    """Classifies user queries into appropriate intent categories"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()
        self.logger = logging.getLogger("catalyze.intent_classifier")
        
        # Define keywords and patterns for each intent
        self.intent_patterns = {
            IntentType.RESEARCH: {
                "keywords": [
                    "what is", "explain", "how does", "tell me about", "describe",
                    "molecular weight", "formula", "structure", "properties",
                    "mechanism", "reaction", "compound", "chemical", "molecule",
                    "find", "search", "lookup", "information", "data"
                ],
                "patterns": [
                    r"what is the (molecular weight|formula|structure) of",
                    r"explain the (mechanism|process|reaction) of",
                    r"tell me about (.*) (compound|chemical|molecule)",
                    r"how does (.*) work",
                    r"find (similar|related) (compounds|chemicals)"
                ]
            },
            IntentType.PROTOCOL: {
                "keywords": [
                    "protocol", "procedure", "steps", "method", "synthesis",
                    "extract", "purify", "isolate", "prepare", "make",
                    "step by step", "how to", "procedure for", "method for",
                    "synthesize", "create", "generate", "produce"
                ],
                "patterns": [
                    r"how to (synthesize|extract|purify|isolate)",
                    r"protocol for (.*)",
                    r"step by step (procedure|method)",
                    r"create a (protocol|procedure) for",
                    r"generate a (method|protocol)"
                ]
            },
            IntentType.AUTOMATE: {
                "keywords": [
                    "opentrons", "ot-2", "ot2", "flex", "protocol", "pipette",
                    "liquid handling", "automation", "robot", "robotic",
                    "automate", "script", "code", "program", "pyhamilton",
                    "96-well", "plate", "transfer", "dispense", "aspirate"
                ],
                "patterns": [
                    r"opentrons (protocol|script|code)",
                    r"generate (opentrons|ot-2|flex) (protocol|script)",
                    r"automate (.*) (process|procedure)",
                    r"create (.*) (script|code|program)",
                    r"liquid handling (protocol|script)"
                ]
            },
            IntentType.SAFETY: {
                "keywords": [
                    "safety", "hazard", "dangerous", "toxic", "corrosive",
                    "ppe", "gloves", "goggles", "lab coat", "fume hood",
                    "sds", "safety data sheet", "risk", "precaution",
                    "incompatible", "reactive", "flammable", "explosive"
                ],
                "patterns": [
                    r"is (.*) (safe|dangerous|toxic)",
                    r"safety (precautions|measures) for",
                    r"what (ppe|safety equipment) for",
                    r"hazard (assessment|analysis) of",
                    r"safety data sheet for"
                ]
            }
        }
    
    async def classify(self, query: str, context: Dict[str, Any] = None) -> ClassificationResult:
        """
        Classify a user query into intent categories
        
        Args:
            query: User's query string
            context: Additional context (conversation history, etc.)
            
        Returns:
            ClassificationResult with intent, confidence, and reasoning
        """
        self.logger.info(f"Classifying query: {query[:100]}...")
        
        # Step 1: Rule-based classification
        rule_result = self._rule_based_classification(query)
        
        # Step 2: LLM-based classification for complex cases
        if rule_result.confidence < 0.7:
            llm_result = await self._llm_based_classification(query, context)
            # Combine results
            final_result = self._combine_classifications(rule_result, llm_result)
        else:
            final_result = rule_result
        
        # Step 3: Extract entities
        entities = self._extract_entities(query)
        final_result.entities = entities
        
        self.logger.info(f"Classification result: {final_result.intent.value} (confidence: {final_result.confidence:.2f})")
        return final_result
    
    def _rule_based_classification(self, query: str) -> ClassificationResult:
        """Rule-based classification using keywords and patterns"""
        query_lower = query.lower()
        
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            
            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in query_lower:
                    score += 1.0
            
            # Check regex patterns
            for pattern in patterns["patterns"]:
                if re.search(pattern, query_lower):
                    score += 2.0  # Patterns are more specific than keywords
            
            intent_scores[intent_type] = score
        
        # Find the best match
        if not intent_scores or max(intent_scores.values()) == 0:
            return ClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities=[],
                reasoning="No matching patterns found"
            )
        
        best_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[best_intent]
        
        # Calculate confidence (normalize by query length and pattern complexity)
        confidence = min(max_score / (len(query.split()) * 0.5), 1.0)
        
        # Get secondary intents
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        secondary_intents = [(intent, score / max_score) for intent, score in sorted_intents[1:3] if score > 0]
        
        return ClassificationResult(
            intent=best_intent,
            confidence=confidence,
            entities=[],
            reasoning=f"Rule-based classification: {best_intent.value} (score: {max_score})",
            secondary_intents=secondary_intents
        )
    
    async def _llm_based_classification(self, query: str, context: Dict[str, Any] = None) -> ClassificationResult:
        """LLM-based classification for complex queries"""
        try:
            # Create classification prompt
            prompt = self._create_classification_prompt(query, context)
            
            # Get LLM response
            response = await self._get_llm_response(prompt)
            
            # Parse LLM response
            return self._parse_llm_classification(response, query)
            
        except Exception as e:
            self.logger.error(f"LLM classification failed: {e}")
            return ClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities=[],
                reasoning=f"LLM classification failed: {str(e)}"
            )
    
    def _create_classification_prompt(self, query: str, context: Dict[str, Any] = None) -> str:
        """Create a prompt for LLM-based classification"""
        context_str = ""
        if context and context.get("conversation_history"):
            context_str = f"\nConversation context: {context['conversation_history'][-3:]}"
        
        prompt = f"""
Classify the following chemistry/lab query into one of these categories:

1. RESEARCH: Questions about chemical properties, mechanisms, explanations, compound lookups
2. PROTOCOL: Requests for lab procedures, synthesis methods, experimental protocols
3. AUTOMATE: Requests for lab automation scripts, Opentrons protocols, robotic systems
4. SAFETY: Safety questions, hazard assessments, PPE recommendations

Query: "{query}"
{context_str}

Respond with a JSON object containing:
{{
    "intent": "research|protocol|automate|safety",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of classification",
    "entities": ["list", "of", "extracted", "entities"]
}}

Consider:
- Research: "What is the molecular weight of caffeine?", "Explain PCR mechanism"
- Protocol: "How to synthesize aspirin?", "Create a protein extraction protocol"
- Automate: "Generate Opentrons protocol for liquid handling", "Automate 96-well plate filling"
- Safety: "Is this chemical combination safe?", "What PPE for this experiment?"
"""
        return prompt
    
    async def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM"""
        try:
            response = self.llm_client.generate_response(
                prompt=prompt,
                system_message="You are an expert at classifying chemistry and lab-related queries. Always respond with valid JSON."
            )
            return response
        except Exception as e:
            self.logger.error(f"LLM response failed: {e}")
            return '{"intent": "unknown", "confidence": 0.0, "reasoning": "LLM error", "entities": []}'
    
    def _parse_llm_classification(self, response: str, query: str) -> ClassificationResult:
        """Parse LLM classification response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                intent_str = data.get("intent", "unknown").lower()
                intent_map = {
                    "research": IntentType.RESEARCH,
                    "protocol": IntentType.PROTOCOL,
                    "automate": IntentType.AUTOMATE,
                    "safety": IntentType.SAFETY
                }
                intent = intent_map.get(intent_str, IntentType.UNKNOWN)
                
                return ClassificationResult(
                    intent=intent,
                    confidence=float(data.get("confidence", 0.0)),
                    entities=data.get("entities", []),
                    reasoning=data.get("reasoning", "LLM classification")
                )
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            return ClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities=[],
                reasoning=f"Failed to parse LLM response: {str(e)}"
            )
    
    def _combine_classifications(self, rule_result: ClassificationResult, llm_result: ClassificationResult) -> ClassificationResult:
        """Combine rule-based and LLM-based classifications"""
        # Weight the results (rule-based gets higher weight for high confidence)
        if rule_result.confidence > 0.8:
            weight_rule = 0.7
            weight_llm = 0.3
        else:
            weight_rule = 0.4
            weight_llm = 0.6
        
        # If both agree, use higher confidence
        if rule_result.intent == llm_result.intent:
            combined_confidence = max(rule_result.confidence, llm_result.confidence)
            return ClassificationResult(
                intent=rule_result.intent,
                confidence=combined_confidence,
                entities=llm_result.entities or rule_result.entities,
                reasoning=f"Combined: {rule_result.reasoning} + {llm_result.reasoning}"
            )
        
        # If they disagree, use the one with higher confidence
        if rule_result.confidence > llm_result.confidence:
            return rule_result
        else:
            return llm_result
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract relevant entities from the query"""
        entities = []
        
        # Chemical names (basic pattern)
        chemical_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Two-word chemicals
            r'\b[A-Z][a-z]+\b',  # Single word chemicals
        ]
        
        for pattern in chemical_patterns:
            matches = re.findall(pattern, query)
            entities.extend(matches)
        
        # Numbers and units
        number_patterns = [
            r'\d+\s*(mg|g|kg|ml|μl|ul|L|M|mM|μM|uM|°C|C)',
            r'\d+\.\d+\s*(mg|g|kg|ml|μl|ul|L|M|mM|μM|uM|°C|C)'
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Remove duplicates and return
        return list(set(entities))
    
    def get_intent_description(self, intent: IntentType) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            IntentType.RESEARCH: "Chemistry research questions, explanations, and compound lookups",
            IntentType.PROTOCOL: "Lab protocol generation and experimental procedures",
            IntentType.AUTOMATE: "Lab automation scripts and robotic systems",
            IntentType.SAFETY: "Safety analysis and hazard assessment",
            IntentType.UNKNOWN: "Unable to classify query"
        }
        return descriptions.get(intent, "Unknown intent")


# Example usage and testing
async def test_intent_classifier():
    """Test the intent classifier with sample queries"""
    classifier = IntentClassifier()
    
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
    
    print("🧪 Testing Intent Classifier...")
    for query in test_queries:
        result = await classifier.classify(query)
        print(f"Query: {query}")
        print(f"Intent: {result.intent.value} (confidence: {result.confidence:.2f})")
        print(f"Entities: {result.entities}")
        print(f"Reasoning: {result.reasoning}")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_intent_classifier())
