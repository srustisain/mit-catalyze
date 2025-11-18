"""
Pipeline Manager

Main orchestrator for the Catalyze agent system. Handles query routing,
agent coordination, and response management.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents import RouterAgent, ResearchAgent, ProtocolAgent, AutomateAgent, SafetyAgent

# Try to import Langfuse decorator
try:
    from langfuse.decorators import observe
except ImportError:
    # Create a no-op decorator if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])


class PipelineManager:
    """Main pipeline orchestrator for the Catalyze system"""
    
    def __init__(self):
        self.logger = logging.getLogger("catalyze.pipeline")
        
        # Initialize agents
        self.router_agent = RouterAgent()
        self.research_agent = ResearchAgent()
        self.protocol_agent = ProtocolAgent()
        self.automate_agent = AutomateAgent()
        self.safety_agent = SafetyAgent()
        
        # Agent registry
        self.agents = {
            "research": self.research_agent,
            "protocol": self.protocol_agent,
            "automate": self.automate_agent,
            "safety": self.safety_agent
        }
        
        # Initialize agents
        self._initialized = False
    
    async def initialize(self):
        """Initialize all agents at startup - eliminates per-query initialization latency"""
        if self._initialized:
            return
        
        try:
            self.logger.debug("Initializing Catalyze pipeline...")
            
            # Initialize router agent's internal agents (SmartRouter pattern)
            if hasattr(self.router_agent, 'initialize_agents'):
                await self.router_agent.initialize_agents()
            
            # Initialize standalone agents in parallel
            await asyncio.gather(
                self.research_agent.initialize(),
                self.protocol_agent.initialize(),
                self.automate_agent.initialize(),
                self.safety_agent.initialize()
            )
            
            self._initialized = True
            self.logger.info("Pipeline initialization complete")
            
        except Exception as e:
            self.logger.error(f"Pipeline initialization failed: {e}")
            raise
    
    @observe()
    async def process_query(self, query: str, mode: str = "research", context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query through the appropriate agent pipeline
        
        Args:
            query: The user's query
            mode: The current mode (research, protocol, automate, safety)
            context: Additional context (conversation history, etc.)
            
        Returns:
            Dictionary containing the response and metadata
        """
        
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        # Store original query for routing (before any modifications)
        original_query = query
        # Remove platform/language suffixes that might have been added
        if " (platform: " in query:
            original_query = query.split(" (platform: ")[0]
        if " (language: " in query:
            original_query = original_query.split(" (language: ")[0]
        
        self.logger.info(f"Processing query in {mode} mode: {original_query[:50]}...")
        if original_query != query:
            self.logger.debug(f"Query modified from '{original_query}' to '{query}' - using original for routing")
        
        try:
            # Step 1: Always check if query explicitly requests a mode
            is_explicit = self._is_explicit_mode_query(original_query)
            self.logger.info(f"PIPELINE: Frontend mode={mode}, is_explicit_mode_query={is_explicit} for query: {original_query[:100]}")
            
            # Step 1.5: Override frontend mode if query doesn't match the selected mode
            # This fixes the issue where frontend sends mode="automate" based on UI tab, even for research queries
            should_override_mode = False
            if mode == "automate" and not is_explicit:
                # Check if query is clearly NOT an automation query
                query_lower = original_query.lower()
                research_indicators = ["what is", "what's", "tell me", "find out", "explain", "describe", "chembl", "chebi", "pubchem", "cas", "solubility", "molecular weight", "formula", "structure", "properties"]
                protocol_indicators = ["protocol", "procedure", "steps", "synthesis", "extract", "how to"]
                safety_indicators = ["safety", "hazard", "dangerous", "toxic", "is safe", "ppe"]
                
                has_research = any(ind in query_lower for ind in research_indicators)
                has_protocol = any(ind in query_lower for ind in protocol_indicators)
                has_safety = any(ind in query_lower for ind in safety_indicators)
                
                # If query has research/protocol/safety indicators but no automation keywords, override mode
                if (has_research or has_protocol or has_safety) and not any(kw in query_lower for kw in [
                    "generate code", "write code", "create code", "opentrons code", "opentrons script",
                    "automation code", "python code", "write script", "generate script"
                ]):
                    should_override_mode = True
                    self.logger.warning(f"PIPELINE: Frontend sent mode='automate' but query is clearly {('research' if has_research else 'protocol' if has_protocol else 'safety')}. Overriding to route through intent classifier.")
                    mode = "research"  # Force routing through intent classifier
            
            # Step 2: Route the query through intent classifier
            # Always route through router if mode is "research" (even if explicit) OR if we overrode the mode
            # The router will correctly classify based on the query content
            if mode == "research" or should_override_mode:
                self.logger.info(f"PIPELINE: Calling router for query: {original_query[:100]}")
                routing_decision = await self.router_agent.process_query(original_query, context)
                
                # Log routing decision with full details
                routed_intent = "unknown"
                routed_confidence = 0.0
                if routing_decision.get("metadata"):
                    routed_intent = routing_decision.get("metadata", {}).get("intent", "unknown")
                    routed_confidence = routing_decision.get("metadata", {}).get("confidence", 0.0)
                    self.logger.info(f"PIPELINE: Router classified as: {routed_intent} (confidence: {routed_confidence:.2f})")
                else:
                    self.logger.warning(f"PIPELINE: Router response missing metadata: {routing_decision.keys()}")
                
                # Defensive check: If router says AUTOMATE but query doesn't have explicit automation keywords, default to research
                if routed_intent == "automate":
                    has_automation_keywords = any(kw in original_query.lower() for kw in [
                        "generate code", "write code", "create code", "opentrons code", "opentrons script",
                        "automation code", "python code", "write script", "generate script"
                    ])
                    if not has_automation_keywords:
                        self.logger.warning(f"PIPELINE: Router classified as AUTOMATE but query has no automation keywords. Overriding to RESEARCH.")
                        routed_intent = "research"
                
                # If the router successfully processed the query, return its response
                if routing_decision.get("success") and routing_decision.get("response"):
                    self.logger.info(f"PIPELINE: Router processed query directly with {routed_intent} agent")
                    return {
                        "success": routing_decision.get("success", True),
                        "response": routing_decision.get("response", "No response generated"),
                        "agent_used": routed_intent,
                        "mode": routed_intent,
                        "used_mcp": routing_decision.get("agent_response", {}).get("used_mcp", False),
                        "timestamp": routing_decision.get("agent_response", {}).get("timestamp", datetime.now().isoformat()),
                        "processing_time": (datetime.now() - start_time).total_seconds()
                    }
                else:
                    # Fallback to suggested agent
                    suggested_agent = routed_intent if routed_intent != "unknown" else mode
                    if suggested_agent != mode:
                        self.logger.info(f"PIPELINE: Router suggested {suggested_agent} instead of {mode}, updating mode")
                        mode = suggested_agent
                    else:
                        self.logger.info(f"PIPELINE: Router suggested {suggested_agent}, keeping mode as {mode}")
            elif mode != "research" and not should_override_mode:
                # Only skip router if mode is explicitly set AND query matches that mode
                if is_explicit:
                    self.logger.info(f"PIPELINE: Skipping router - mode is {mode} and query explicitly requests this mode")
                else:
                    # Mode doesn't match query - force routing
                    self.logger.warning(f"PIPELINE: Mode is {mode} but query doesn't explicitly request it. Forcing routing through intent classifier.")
                    mode = "research"
                    # Recursively call router (but only once to avoid infinite loop)
                    routing_decision = await self.router_agent.process_query(original_query, context)
                    if routing_decision.get("metadata"):
                        routed_intent = routing_decision.get("metadata", {}).get("intent", mode)
                        mode = routed_intent
                        self.logger.info(f"PIPELINE: Router reclassified as: {routed_intent}")
            
            # Step 2: Process with the appropriate agent
            # Use original query for agent processing (agents can handle platform detection themselves)
            self.logger.info(f"PIPELINE: Processing with agent for mode: {mode}")
            agent = self.agents.get(mode, self.research_agent)
            if agent is None:
                self.logger.warning(f"PIPELINE: Agent for mode '{mode}' not found, falling back to research_agent")
                agent = self.research_agent
                mode = "research"
            result = await agent.process_query(original_query, context)
            
            # Step 3: Format the response
            response_data = {
                "success": result.get("success", True),
                "response": result.get("response", "No response generated"),
                "agent_used": result.get("agent", mode),
                "mode": mode,
                "used_mcp": result.get("used_mcp", False),
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
            # Add error information if present
            if not result.get("success"):
                response_data["error"] = result.get("error", "Unknown error")
            
            self.logger.info(f"Query processed successfully by {mode} agent in {response_data['processing_time']:.2f}s")
            return response_data
            
        except Exception as e:
            self.logger.error(f"Pipeline processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, I encountered an error processing your request. Please try again.",
                "agent_used": mode,
                "mode": mode,
                "used_mcp": False,
                "timestamp": datetime.now().isoformat(),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _is_explicit_mode_query(self, query: str) -> bool:
        """Check if the query explicitly requests a specific mode (other than research)"""
        query_lower = query.lower()
        
        # Only bypass routing for VERY explicit automation/protocol/safety requests
        # These must be exact phrases, not just containing words
        explicit_automation = [
            "write code", "generate code", "create code", "write script", "generate script",
            "opentrons protocol", "opentrons code", "automation script", "automation code",
            "python code", "c# code", "csharp code"
        ]
        explicit_protocol = [
            "generate a protocol", "create a protocol", "write a protocol",
            "step-by-step protocol", "detailed protocol", "synthesis protocol"
        ]
        explicit_safety = [
            "safety analysis", "hazard assessment", "safety information", "safety data"
        ]
        
        # Check for explicit mode indicators
        has_automation = any(indicator in query_lower for indicator in explicit_automation)
        has_protocol = any(indicator in query_lower for indicator in explicit_protocol)
        has_safety = any(indicator in query_lower for indicator in explicit_safety)
        
        result = has_automation or has_protocol or has_safety
        if result:
            matched = []
            if has_automation:
                matched.extend([kw for kw in explicit_automation if kw in query_lower])
            if has_protocol:
                matched.extend([kw for kw in explicit_protocol if kw in query_lower])
            if has_safety:
                matched.extend([kw for kw in explicit_safety if kw in query_lower])
            self.logger.info(f"PIPELINE: _is_explicit_mode_query=True, matched keywords: {matched}")
        
        # Only bypass routing if there's a clear, explicit mode request
        return result
    
    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get information about all available agents"""
        return {
            "research": {
                "name": "Research Agent",
                "description": "Handles chemistry research questions and explanations",
                "tools": self.research_agent.tools
            },
            "protocol": {
                "name": "Protocol Agent", 
                "description": "Generates lab protocols and experimental procedures",
                "tools": self.protocol_agent.tools
            },
            "automate": {
                "name": "Automate Agent",
                "description": "Creates automation scripts for lab equipment",
                "tools": self.automate_agent.tools
            },
            "safety": {
                "name": "Safety Agent",
                "description": "Analyzes safety hazards and provides safety information",
                "tools": self.safety_agent.tools
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status information"""
        return {
            "initialized": self._initialized,
            "agents_available": list(self.agents.keys()),
            "total_agents": len(self.agents)
        }
