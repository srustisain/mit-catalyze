"""
Router Agent

Analyzes incoming queries and routes them to the appropriate specialist agent.
Uses OpenAI to classify queries based on intent and content.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class RouterAgent(BaseAgent):
    """Routes queries to appropriate specialist agents"""
    
    def __init__(self):
        super().__init__(
            name="RouterAgent",
            description="Analyzes queries and routes them to the most appropriate specialist agent"
        )
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route the query to the appropriate specialist agent"""
        
        # Get the routing decision
        routing_decision = await self._classify_query(query, context)
        
        return {
            "success": True,
            "routing_decision": routing_decision,
            "agent": self.name,
            "timestamp": self._get_timestamp()
        }
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def _classify_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Classify the query and determine the best agent to handle it"""
        
        # Get the current mode from context if available
        current_mode = context.get("mode", "research") if context else "research"
        
        # Define agent capabilities
        agent_capabilities = {
            "research": {
                "keywords": ["what is", "explain", "tell me about", "how does", "why", "properties", "structure", "formula", "molecular weight", "chemical", "compound", "molecule", "element"],
                "description": "Handles chemistry research questions, explanations, and general chemistry knowledge"
            },
            "protocol": {
                "keywords": ["protocol", "procedure", "steps", "method", "experiment", "synthesis", "reaction", "lab", "procedure", "how to make", "how to synthesize"],
                "description": "Generates lab protocols, experimental procedures, and step-by-step methods"
            },
            "automate": {
                "keywords": ["automate", "script", "robot", "opentrons", "pyhamilton", "automation", "pipette", "liquid handling", "lab automation"],
                "description": "Creates automation scripts for lab equipment and robotic systems"
            },
            "safety": {
                "keywords": ["safety", "hazard", "dangerous", "toxic", "flammable", "corrosive", "safety data sheet", "sds", "risk", "precautions", "ppe"],
                "description": "Analyzes safety hazards and provides safety information"
            }
        }
        
        # Create classification prompt
        classification_prompt = f"""
Analyze this chemistry query and determine which specialist agent should handle it:

Query: "{query}"
Current Mode: {current_mode}

Available Agents:
"""
        
        for mode, info in agent_capabilities.items():
            classification_prompt += f"""
- {mode.upper()}: {info['description']}
  Keywords: {', '.join(info['keywords'][:5])}...
"""
        
        classification_prompt += f"""

Consider both the explicit mode ({current_mode}) and the query content.
Respond with ONLY the agent name (research, protocol, automate, or safety) and a brief reason.

Format: AGENT_NAME: reason
"""
        
        try:
            # Use OpenAI to classify the query
            response = self.llm_client.generate_chat_response(classification_prompt, [])
            
            # Parse the response
            agent_name = self._parse_agent_response(response)
            
            # Validate the agent name
            if agent_name not in agent_capabilities:
                agent_name = current_mode  # Fallback to current mode
            
            return {
                "agent": agent_name,
                "confidence": "high",
                "reasoning": response,
                "current_mode": current_mode
            }
            
        except Exception as e:
            # Fallback to current mode if classification fails
            return {
                "agent": current_mode,
                "confidence": "low",
                "reasoning": f"Classification failed: {str(e)}",
                "current_mode": current_mode
            }
    
    def _parse_agent_response(self, response: str) -> str:
        """Parse the agent response to extract the agent name"""
        response_lower = response.lower().strip()
        
        # Look for agent names in the response
        agents = ["research", "protocol", "automate", "safety"]
        
        for agent in agents:
            if agent in response_lower:
                return agent
        
        # Default to research if no clear match
        return "research"
    
    def get_system_prompt(self) -> str:
        return """You are a query routing specialist for Catalyze, an AI chemistry assistant.

Your job is to analyze chemistry-related queries and determine which specialist agent should handle them:

1. RESEARCH: General chemistry questions, explanations, properties, structures
2. PROTOCOL: Lab procedures, experimental methods, synthesis steps  
3. AUTOMATE: Lab automation scripts, robotic systems, equipment control
4. SAFETY: Safety hazards, risk assessment, safety data, precautions

Always consider both the user's current mode and the query content to make the best routing decision."""
