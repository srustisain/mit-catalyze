"""
LangChain-based Intent Classification

Uses LangChain's built-in classification tools for more sophisticated intent detection.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.clients.llm_client import LLMClient
from src.config.logging_config import get_logger


class IntentType(Enum):
    RESEARCH = "research"
    PROTOCOL = "protocol"
    AUTOMATE = "automate"
    SAFETY = "safety"
    UNKNOWN = "unknown"


class ClassificationResult(BaseModel):
    """Pydantic model for structured output"""
    intent: str = Field(description="The classified intent")
    confidence: float = Field(description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Explanation for the classification")
    entities: List[str] = Field(description="Extracted entities from the query")


class LangChainIntentClassifier:
    """Intent classifier using LangChain's built-in tools"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()
        self.logger = get_logger("catalyze.langchain_classifier")
        
        # Initialize LangChain components
        self._setup_classifier()
        self._setup_entity_extractor()
        self._setup_output_parser()
    
    def _setup_classifier(self):
        """Setup the LangChain text classifier"""
        # Create a custom classifier using LLMChain
        self.classifier = LLMChain(
            llm=self.llm_client.openai_client,
            prompt=self._create_classification_prompt()
        )
    
    def _setup_entity_extractor(self):
        """Setup entity extraction using LangChain"""
        entity_prompt = PromptTemplate(
            input_variables=["query"],
            template="""
Extract relevant entities from this chemistry query: {query}

Return a JSON list of entities including:
- Chemical names (e.g., "caffeine", "aspirin", "benzene")
- Numbers with units (e.g., "100μL", "2.5M", "37°C")
- Equipment names (e.g., "Opentrons", "OT-2", "96-well plate")
- Process names (e.g., "PCR", "synthesis", "extraction")

Format: ["entity1", "entity2", "entity3"]
"""
        )
        
        self.entity_chain = LLMChain(
            llm=self.llm_client.openai_client,
            prompt=entity_prompt
        )
    
    def _setup_output_parser(self):
        """Setup Pydantic output parser for structured responses"""
        self.output_parser = PydanticOutputParser(pydantic_object=ClassificationResult)
    
    def _create_classification_prompt(self) -> PromptTemplate:
        """Create a sophisticated classification prompt"""
        return PromptTemplate(
            input_variables=["text"],
            template="""
You are an expert chemistry query classifier. Classify the following query into one of these categories:

1. RESEARCH: Questions about chemical properties, mechanisms, explanations, compound lookups
   Examples: "What is the molecular weight of caffeine?", "Explain PCR mechanism", "Tell me about aspirin structure"

2. PROTOCOL: Requests for lab procedures, synthesis methods, experimental protocols
   Examples: "How do I synthesize aspirin?", "Create a protein extraction protocol", "What's the procedure for DNA isolation?"

3. AUTOMATE: Requests for lab automation scripts, robotic systems, equipment control
   Examples: "Generate Opentrons protocol for liquid handling", "Create PyHamilton script", "Automate 96-well plate filling"

4. SAFETY: Safety questions, hazard assessments, PPE recommendations
   Examples: "Is this chemical combination safe?", "What PPE for this experiment?", "Check SDS for benzene"

Query: {text}

Consider:
- The primary intent of the query
- The type of response the user is seeking
- The context and domain of the question
- Any specific equipment or processes mentioned

Respond with only the category name (research, protocol, automate, or safety).
"""
        )
    
    async def classify(self, query: str, context: Dict[str, Any] = None) -> ClassificationResult:
        """
        Classify a user query using LangChain's built-in tools
        
        Args:
            query: User's query string
            context: Additional context (conversation history, etc.)
            
        Returns:
            ClassificationResult with intent, confidence, and reasoning
        """
        self.logger.info(f"Classifying query with LangChain: {query[:100]}...")
        
        try:
            # Step 1: Use LangChain's TextClassifier
            classification_result = await self._classify_with_langchain(query)
            
            # Step 2: Extract entities using LangChain
            entities = await self._extract_entities_with_langchain(query)
            
            # Step 3: Calculate confidence based on multiple factors
            confidence = await self._calculate_confidence(query, classification_result, entities)
            
            # Step 4: Generate reasoning
            reasoning = await self._generate_reasoning(query, classification_result, entities, confidence)
            
            return ClassificationResult(
                intent=classification_result,
                confidence=confidence,
                reasoning=reasoning,
                entities=entities
            )
            
        except Exception as e:
            self.logger.error(f"LangChain classification failed: {e}")
            return ClassificationResult(
                intent="unknown",
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}",
                entities=[]
            )
    
    async def _classify_with_langchain(self, query: str) -> str:
        """Use LangChain's LLMChain for classification"""
        try:
            # Use the classifier
            result = await self.classifier.arun(text=query)
            # Extract category from result
            result_lower = result.lower().strip()
            for category in ["research", "protocol", "automate", "safety"]:
                if category in result_lower:
                    return category
            return "unknown"
        except Exception as e:
            self.logger.error(f"LangChain classifier failed: {e}")
            return "unknown"
    
    async def _extract_entities_with_langchain(self, query: str) -> List[str]:
        """Extract entities using LangChain"""
        try:
            result = await self.entity_chain.arun(query=query)
            # Parse JSON result
            import json
            entities = json.loads(result)
            return entities if isinstance(entities, list) else []
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
            return []
    
    async def _calculate_confidence(self, query: str, classification: str, entities: List[str]) -> float:
        """Calculate confidence score using multiple factors"""
        try:
            # Factor 1: Query length and specificity
            query_length_factor = min(len(query.split()) / 10, 1.0)
            
            # Factor 2: Entity relevance
            entity_factor = min(len(entities) / 5, 1.0)
            
            # Factor 3: Classification certainty (using LLM)
            certainty_prompt = f"""
Rate the certainty of this classification on a scale of 0-1:

Query: "{query}"
Classification: "{classification}"
Entities: {entities}

Consider:
- How clear and specific the query is
- How well the entities match the classification
- Whether the query has multiple possible interpretations

Respond with only a number between 0 and 1.
"""
            
            certainty_response = await self.llm_client.generate_response(certainty_prompt)
            try:
                certainty = float(certainty_response.strip())
            except:
                certainty = 0.5
            
            # Combine factors
            confidence = (query_length_factor * 0.3 + entity_factor * 0.3 + certainty * 0.4)
            return min(max(confidence, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    async def _generate_reasoning(self, query: str, classification: str, entities: List[str], confidence: float) -> str:
        """Generate reasoning for the classification"""
        try:
            reasoning_prompt = f"""
Explain why this query was classified as "{classification}":

Query: "{query}"
Entities: {entities}
Confidence: {confidence:.2f}

Provide a brief, clear explanation of the classification reasoning.
"""
            
            reasoning = await self.llm_client.generate_response(reasoning_prompt)
            return reasoning.strip()
            
        except Exception as e:
            self.logger.error(f"Reasoning generation failed: {e}")
            return f"Classified as {classification} with {confidence:.2f} confidence"
    
    async def classify_batch(self, queries: List[str]) -> List[ClassificationResult]:
        """Classify multiple queries in batch"""
        results = []
        for query in queries:
            result = await self.classify(query)
            results.append(result)
        return results
    
    async def get_classification_stats(self) -> Dict[str, Any]:
        """Get statistics about the classifier"""
        return {
            "classifier_type": "LangChain TextClassifier",
            "llm_provider": self.llm_client.provider,
            "categories": ["research", "protocol", "automate", "safety"],
            "features": [
                "LangChain TextClassifier",
                "Entity extraction",
                "Confidence scoring",
                "Reasoning generation",
                "Batch processing"
            ]
        }


# Example usage and testing
async def test_langchain_classifier():
    """Test the LangChain-based classifier"""
    classifier = LangChainIntentClassifier()
    
    test_queries = [
        "What is the molecular weight of caffeine?",
        "How do I synthesize aspirin?",
        "Generate an Opentrons protocol for liquid handling",
        "Is this chemical combination safe?",
        "Explain the mechanism of PCR",
        "Create a protein extraction protocol"
    ]
    
    logger = get_logger("catalyze.test.langchain_classifier")
    logger.info("🧪 Testing LangChain Intent Classifier...")
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        result = await classifier.classify(query)
        logger.info(f"Intent: {result.intent}")
        logger.info(f"Confidence: {result.confidence:.2f}")
        logger.info(f"Entities: {result.entities}")
        logger.info(f"Reasoning: {result.reasoning}")
        logger.info("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_langchain_classifier())
