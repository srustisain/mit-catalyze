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
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re

from src.config.logging_config import get_logger


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
    confidence: float  # 1.0 if matched, 0.0 if not matched
    entities: List[str]
    reasoning: str


class IntentClassifier:
    """Classifies user queries into appropriate intent categories using simple priority-based matching"""
    
    def __init__(self, llm_client=None):
        # llm_client parameter kept for backward compatibility but not used
        self.logger = get_logger("catalyze.intent_classifier")
        
        # Define explicit keywords for each intent (priority order: automate > protocol > safety > research)
        # Only the most explicit keywords that clearly indicate intent
        self.automate_keywords = [
            "generate code", "write code", "create code", "make code",
            "generate script", "write script", "create script", "make script",
            "opentrons code", "opentrons script", "opentrons protocol",
            "generate opentrons", "create opentrons", "write opentrons",
            "lynx code", "lynx script",
            "automation code", "automation script",
            "python code", "c# code", "csharp code",
            "code for", "script for"  # "code for this protocol" pattern
        ]
        
        self.protocol_keywords = [
            "create protocol", "generate protocol", "write protocol",
            "create procedure", "generate procedure", "write procedure",
            "laboratory protocol", "lab protocol", "experimental protocol",
            "synthesis protocol", "extraction protocol",
            "step by step protocol", "step-by-step protocol",
            "complete protocol", "detailed protocol"
        ]
        
        self.safety_keywords = [
            "safety analysis", "safety assessment", "safety data",
            "hazard analysis", "hazard assessment",
            "is safe", "is dangerous", "is toxic",
            "safety precautions", "safety measures",
            "ppe for", "safety equipment"
        ]
    
    async def classify(self, query: str, context: Dict[str, Any] = None) -> ClassificationResult:
        """
        Classify a user query into intent categories using simple priority-based matching.
        Defaults to RESEARCH if no explicit intent is found.
        
        Args:
            query: User's query string
            context: Additional context (conversation history, etc.) - not used in simple classification
            
        Returns:
            ClassificationResult with intent, confidence, and reasoning
        """
        self.logger.info(f"Classifying query: {query[:100]}...")
        
        # Step 0: Content guardrails - check if query is chemistry/lab related
        if not self._is_chemistry_related(query):
            self.logger.warning(f"Query rejected by guardrails: {query[:50]}...")
            return ClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=1.0,
                reasoning="Query is not chemistry or lab-related",
                entities=[]
            )
        
        # Step 1: Simple priority-based classification
        result = self._simple_classify(query)
        
        # Step 2: Extract entities
        entities = self._extract_entities(query)
        result.entities = entities
        
        self.logger.info(f"Classification result: {result.intent.value} (confidence: {result.confidence:.2f})")
        return result
    
    def _simple_classify(self, query: str) -> ClassificationResult:
        """
        Simple priority-based classification.
        Checks for explicit keywords in priority order: automate > protocol > safety > research (default)
        Uses flexible matching that allows words between keyword parts.
        """
        query_lower = query.lower()
        
        # Log all keywords being checked for debugging
        self.logger.debug(f"INTENT CLASSIFIER: Checking query '{query[:100]}' against {len(self.automate_keywords)} automation, {len(self.protocol_keywords)} protocol, {len(self.safety_keywords)} safety keywords")
        
        # Priority 1: Check for explicit automation keywords
        matched_automate = []
        for keyword in self.automate_keywords:
            # Try exact match first
            if keyword in query_lower:
                matched_automate.append(keyword)
            else:
                # Flexible matching: check if all words in keyword appear in order
                keyword_words = keyword.split()
                if len(keyword_words) > 1:
                    # For multi-word keywords, check if all words appear in order (allowing words in between)
                    pattern = r'\b' + r'\b.*\b'.join(re.escape(word) for word in keyword_words) + r'\b'
                    if re.search(pattern, query_lower):
                        matched_automate.append(keyword)
        
        if matched_automate:
            self.logger.info(f"INTENT CLASSIFIER: Matched AUTOMATE keywords {matched_automate} in query: {query[:100]}")
            return ClassificationResult(
                intent=IntentType.AUTOMATE,
                confidence=1.0,
                entities=[],
                reasoning=f"Explicit automation keyword matched: {matched_automate[0]}"
            )
        
        # Priority 2: Check for explicit protocol keywords
        matched_protocol = []
        for keyword in self.protocol_keywords:
            # Try exact match first
            if keyword in query_lower:
                matched_protocol.append(keyword)
            else:
                # Flexible matching: check if all words in keyword appear in order
                keyword_words = keyword.split()
                if len(keyword_words) > 1:
                    # For multi-word keywords, check if all words appear in order (allowing words in between)
                    pattern = r'\b' + r'\b.*\b'.join(re.escape(word) for word in keyword_words) + r'\b'
                    if re.search(pattern, query_lower):
                        matched_protocol.append(keyword)
        
        if matched_protocol:
            self.logger.info(f"INTENT CLASSIFIER: Matched PROTOCOL keywords {matched_protocol} in query: {query[:100]}")
            return ClassificationResult(
                intent=IntentType.PROTOCOL,
                confidence=1.0,
                entities=[],
                reasoning=f"Explicit protocol keyword matched: {matched_protocol[0]}"
            )
        
        # Priority 3: Check for explicit safety keywords
        matched_safety = []
        for keyword in self.safety_keywords:
            # Try exact match first
            if keyword in query_lower:
                matched_safety.append(keyword)
            else:
                # Flexible matching: check if all words in keyword appear in order
                keyword_words = keyword.split()
                if len(keyword_words) > 1:
                    # For multi-word keywords, check if all words appear in order (allowing words in between)
                    pattern = r'\b' + r'\b.*\b'.join(re.escape(word) for word in keyword_words) + r'\b'
                    if re.search(pattern, query_lower):
                        matched_safety.append(keyword)
        
        if matched_safety:
            self.logger.info(f"INTENT CLASSIFIER: Matched SAFETY keywords {matched_safety} in query: {query[:100]}")
            return ClassificationResult(
                intent=IntentType.SAFETY,
                confidence=1.0,
                entities=[],
                reasoning=f"Explicit safety keyword matched: {matched_safety[0]}"
            )
        
        # Priority 4: Default to RESEARCH (most chemistry queries are research)
        total_keywords = len(self.automate_keywords) + len(self.protocol_keywords) + len(self.safety_keywords)
        self.logger.info(f"INTENT CLASSIFIER: No explicit intent matched for query '{query[:100]}' (checked {total_keywords} keywords), defaulting to RESEARCH")
        return ClassificationResult(
            intent=IntentType.RESEARCH,
            confidence=1.0,
            entities=[],
            reasoning="Default to research (no explicit intent keywords found)"
        )
    
    
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
    
    def _is_chemistry_related(self, query: str) -> bool:
        """
        Simple check if a query could be related to chemistry or lab work.
        Uses very basic pattern matching and accepts most queries that could be chemistry-related.
        """
        query_lower = query.lower()
        
        # Check for obvious non-chemistry topics that should be rejected
        non_chemistry_indicators = [
            "depression", "anxiety", "mental health", "therapy", "counseling",
            "weather", "sports", "politics", "religion", "philosophy",
            "cooking", "recipe", "food", "restaurant", "travel", "vacation",
            "entertainment", "movie", "music", "book", "game", "hobby",
            "car", "vehicle", "repair", "fix", "maintenance"
        ]
        
        # If it contains obvious non-chemistry topics, reject
        if any(indicator in query_lower for indicator in non_chemistry_indicators):
            return False
        
        # Check for chemistry indicators
        chemistry_indicators = [
            "chemical", "compound", "molecule", "element", "formula", "structure",
            "reaction", "synthesis", "catalyst", "solvent", "reagent", "product",
            "laboratory", "lab", "experiment", "protocol", "procedure", "method",
            "pipette", "beaker", "flask", "centrifuge", "spectrometer",
            "chromatography", "distillation", "extraction", "purification",
            "opentrons", "automation", "liquid handling", "ph", "concentration",
            "molarity", "molar", "mass", "volume", "density", "temperature",
            "pressure", "enzyme", "protein", "dna", "rna", "pcr", "polymerase",
            "safety", "hazard", "toxic", "flammable", "corrosive", "ppe",
            "what is", "how to", "explain", "tell me", "create", "generate",
            "make", "prepare", "analyze", "test", "measure", "calculate",
            "code", "script", "program", "automate", "robot", "robotic", "ot-2", "ot2", "flex",
            "96-well", "plate", "transfer", "dispense", "aspirate", "well", "wells"
        ]
        
        # Check for chemical formulas (capital letter + lowercase + numbers)
        chemical_formulas = re.findall(r'\b[A-Z][a-z]?\d*\b', query)
        
        # Check for lab units
        lab_units = re.findall(r'\b\d+\s*(mg|g|kg|ml|l|ul|μl|molar|m|mm|nm|pm|°c|°f|k|bar|psi|torr|atm)\b', query_lower)
        
        # Check for pH values
        ph_values = re.findall(r'\bph\s*[=:]?\s*\d+\.?\d*\b', query_lower)
        
        chemistry_score = sum(1 for term in chemistry_indicators if term in query_lower)
        formula_score = len(chemical_formulas)
        unit_score = len(lab_units)
        ph_score = len(ph_values)
        
        # Calculate total score
        total_score = chemistry_score + (formula_score * 2) + unit_score + ph_score
        
        # Accept if it has any chemistry indicators, or if it's a general question that could be chemistry-related
        return total_score >= 1 or any(word in query_lower for word in ["what", "how", "explain", "tell", "create", "make", "generate"])


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
    
    logger = get_logger("catalyze.test.intent_classifier")
    logger.info("🧪 Testing Intent Classifier...")
    for query in test_queries:
        result = await classifier.classify(query)
        logger.info(f"Query: {query}")
        logger.info(f"Intent: {result.intent.value} (confidence: {result.confidence:.2f})")
        logger.info(f"Entities: {result.entities}")
        logger.info(f"Reasoning: {result.reasoning}")
        logger.info("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_intent_classifier())
