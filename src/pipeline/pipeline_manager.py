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
        """Initialize all agents"""
        if self._initialized:
            return
        
        try:
            self.logger.info("Initializing Catalyze pipeline...")
            
            # Initialize all agents
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
        self.logger.info(f"Processing query in {mode} mode: {query[:50]}...")
        
        try:
            # Step 1: Route the query (if not already in a specific mode)
            if mode == "research" and not self._is_explicit_mode_query(query):
                routing_decision = await self.router_agent.process_query(query, context)
                suggested_agent = routing_decision.get("routing_decision", {}).get("agent", mode)
                
                # Use suggested agent if it's different from current mode
                if suggested_agent != mode:
                    self.logger.info(f"Router suggested {suggested_agent} instead of {mode}")
                    mode = suggested_agent
            
            # Step 2: Process with the appropriate agent
            agent = self.agents.get(mode, self.research_agent)
            result = await agent.process_query(query, context)
            
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
        """Check if the query explicitly requests a specific mode"""
        query_lower = query.lower()
        
        explicit_indicators = [
            "generate a protocol",
            "create a protocol", 
            "write a script",
            "automate this",
            "safety analysis",
            "hazard assessment",
            "safety information"
        ]
        
        return any(indicator in query_lower for indicator in explicit_indicators)
    
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
