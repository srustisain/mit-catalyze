"""
Smart Router Agent

Intelligent router that classifies user queries and delegates to appropriate specialized agents.
Uses LangGraph for state management and decision flow.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime

from .intent_classifier import IntentClassifier, IntentType, ClassificationResult
from .research_agent import ResearchAgent
from .protocol_agent import ProtocolAgent
from .automate_agent import AutomateAgent
from .safety_agent import SafetyAgent
from src.clients.llm_client import LLMClient
from src.config.logging_config import get_logger


class RouterState(TypedDict):
    """State for the router agent"""
    query: str
    context: Dict[str, Any]
    classification: Optional[ClassificationResult]
    agent_responses: Dict[str, Any]
    final_response: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]


class SmartRouter:
    """Intelligent router agent for query classification and delegation"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()
        self.logger = get_logger("catalyze.smart_router")
        
        # Initialize components
        self.intent_classifier = IntentClassifier(llm_client)
        # Create agent instances once - they'll be initialized on first use or at startup
        self.specialized_agents = {
            IntentType.RESEARCH: ResearchAgent(),
            IntentType.PROTOCOL: ProtocolAgent(),
            IntentType.AUTOMATE: AutomateAgent(),
            IntentType.SAFETY: SafetyAgent()
        }
        self._agents_initialized = False
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query through the router system
        
        Args:
            query: User's query string
            context: Additional context (conversation history, etc.)
            
        Returns:
            Dictionary containing the response and metadata
        """
        self.logger.info(f"Processing query: {query[:100]}...")
        
        try:
            # Step 1: Classify the query
            classification = await self.intent_classifier.classify(query, context)
            self.logger.info(f"Classified as: {classification.intent.value} (confidence: {classification.confidence:.2f})")
            
            # Step 1.5: Check if query was rejected by guardrails
            if classification.intent == IntentType.UNKNOWN and classification.reasoning == "Query is not chemistry or lab-related":
                return {
                    "success": False,
                    "response": "I specialize in chemistry and laboratory work. Please ask me about chemical compounds, lab protocols, automation, or safety procedures.",
                    "classification": classification,
                    "error": "Query rejected by content guardrails"
                }
            
            # Step 2: Route to appropriate agent
            if classification.confidence < 0.3:
                return {
                    "success": False,
                    "response": "I'm not sure how to help with that. Could you please rephrase your question or provide more details?",
                    "classification": classification,
                    "error": f"Low confidence classification: {classification.confidence:.2f}"
                }
            
            # Step 3: Execute the appropriate agent
            if classification.intent == IntentType.UNKNOWN:
                # Handle unknown intents with a helpful default response
                return {
                    "success": True,
                    "response": "Sorry, I can help you with chemistry and lab-related questions! I can assist with:\n\n• **Research questions** - Chemical compounds, reactions, properties\n• **Protocol generation** - Lab procedures and experimental methods\n• **Lab automation** - Opentrons protocols and automation scripts\n• **Safety analysis** - Chemical hazards and safety procedures\n\nPlease ask me something related to chemistry or laboratory work!",
                    "classification": classification,
                    "metadata": {
                        "processed_at": datetime.now().isoformat(),
                        "intent": "unknown",
                        "confidence": classification.confidence
                    }
                }
            
            agent_response = await self._execute_agent(classification.intent, query, context)
            
            # Step 4: Format the response
            final_response = self._format_response(agent_response, classification)
            
            return {
                "success": True,
                "response": final_response,
                "classification": classification,
                "agent_response": agent_response,
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "intent": classification.intent.value,
                    "confidence": classification.confidence
                }
            }
            
        except Exception as e:
            self.logger.error(f"Router processing failed: {e}")
            return {
                "success": False,
                "response": "I apologize, but I encountered an error while processing your query. Please try again.",
                "error": str(e),
                "metadata": {"error_time": datetime.now().isoformat()}
            }
    
    async def initialize_agents(self):
        """Initialize all agents once at startup - reduces per-query latency"""
        if self._agents_initialized:
            return
        
        self.logger.info("Pre-initializing all specialized agents...")
        for intent, agent in self.specialized_agents.items():
            try:
                await agent.initialize()
                self.logger.info(f"✓ {intent.value} agent ready")
            except Exception as e:
                self.logger.error(f"Failed to initialize {intent.value} agent: {e}")
        
        self._agents_initialized = True
        self.logger.info("All agents pre-initialized and ready")
    
    async def _execute_agent(self, intent: IntentType, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate specialized agent (agents are pre-initialized)"""
        try:
            agent = self.specialized_agents.get(intent)
            if not agent:
                return {
                    "success": False,
                    "error": f"No agent available for intent: {intent.value}"
                }
            
            # Agents should already be initialized at startup
            # Process the query directly (no initialization overhead per query)
            response = await agent.process_query(query, context)
            return response
            
        except Exception as e:
            self.logger.error(f"Agent execution failed for {intent.value}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_response(self, agent_response: Dict[str, Any], classification: ClassificationResult) -> str:
        """Format the agent response for the user"""
        try:
            if not agent_response.get("success", False):
                error_msg = agent_response.get("error", "Unknown error")
                return f"I encountered an issue while processing your {classification.intent.value} request: {error_msg}"
            
            # Extract the main response content
            if "response" in agent_response:
                content = agent_response["response"]
            elif "message" in agent_response:
                content = agent_response["message"]
            else:
                content = str(agent_response)
            
            # Add classification context if confidence is low
            if classification.confidence < 0.8:
                context = f"\n\n*Note: I classified this as a {classification.intent.value} question. If this isn't what you were looking for, please let me know!*"
                content += context
            
            return content
            
        except Exception as e:
            self.logger.error(f"Response formatting failed: {e}")
            return "Response received but formatting failed."
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of the router and all agents"""
        status = {
            "router": "active",
            "intent_classifier": "active",
            "specialized_agents": {}
        }
        
        for intent, agent in self.specialized_agents.items():
            try:
                status["specialized_agents"][intent.value] = "available"
            except Exception as e:
                status["specialized_agents"][intent.value] = f"error: {str(e)}"
        
        return status


# Example usage and testing
async def test_smart_router():
    """Test the smart router with sample queries"""
    router = SmartRouter()
    
    test_queries = [
        "What is the molecular weight of caffeine?",
        "How do I synthesize aspirin?",
        "Generate an Opentrons protocol for liquid handling",
        "Is this chemical combination safe?",
        "Explain the mechanism of PCR",
        "Create a protein extraction protocol"
    ]
    
    logger = get_logger("catalyze.test.smart_router")
    logger.info("🧪 Testing Smart Router...")
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        result = await router.process_query(query)
        logger.info(f"Success: {result['success']}")
        logger.info(f"Response: {result['response'][:200]}...")
        if result.get('classification'):
            logger.info(f"Classified as: {result['classification'].intent.value}")
        logger.info("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_smart_router())
