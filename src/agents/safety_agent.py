"""
Safety Agent

Specialized agent for analyzing safety hazards, providing safety information, and risk assessment.
Focuses on chemical safety, hazard identification, and safety protocol recommendations.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class SafetyAgent(BaseAgent):
    """Analyzes safety hazards and provides safety information"""
    
    def __init__(self):
        super().__init__(
            name="SafetyAgent",
            description="Specialized in safety analysis, hazard assessment, and safety protocol recommendations",
            tools=[
                "search_compounds",
                "get_compound_info",
                "search_activities",
                "get_assay_info",
                "search_drugs"
            ]
        )
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze safety hazards and provide safety information"""
        
        # Create a safety-focused prompt
        safety_prompt = f"""
Provide a comprehensive safety analysis for: {query}

Include:
1. Hazard Identification
2. Risk Assessment (High/Medium/Low)
3. Safety Precautions and PPE Requirements
4. Emergency Procedures
5. Storage and Handling Guidelines
6. Disposal Considerations
7. Regulatory Information (if applicable)

Prioritize safety and provide clear, actionable safety guidance.
"""
        
        # Use the LangGraph agent with MCP tools directly
        if self.agent and self.mcp_client:
            try:
                # Let the LangGraph agent handle the query with MCP tools
                agent_result = await self._run_agent_safely(safety_prompt, context)
                
                if agent_result.get("success"):
                    # Extract the response content
                    messages = agent_result.get("response", [])
                    response_content = ""
                    
                    for message in messages:
                        if hasattr(message, 'content') and message.content:
                            response_content += message.content + "\n"
                    
                    return {
                        "success": True,
                        "response": response_content.strip(),
                        "agent": self.name,
                        "used_mcp": True,
                        "timestamp": self._get_timestamp()
                    }
                else:
                    # Fallback to basic LLM response
                    return await self._fallback_response(safety_prompt, context)
                    
            except Exception as e:
                self.logger.error(f"LangGraph agent failed: {e}")
                return await self._fallback_response(safety_prompt, context)
        else:
            # Fallback to basic LLM response if no agent available
            return await self._fallback_response(safety_prompt, context)
    
    async def _fallback_response(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback response when MCP tools are not available"""
        try:
            conversation_history = context.get("conversation_history", []) if context else []
            response = self.llm_client.generate_chat_response(query, conversation_history)
            self.logger.info(f"Generated fallback safety response: {len(response)} characters")
            
            return {
                "success": True,
                "response": response,
                "agent": self.name,
                "used_mcp": False,
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            self.logger.error(f"Fallback response failed: {e}")
            return {
                "success": False,
                "response": "I'm having trouble analyzing safety information right now.",
                "agent": self.name,
                "used_mcp": False,
                "timestamp": self._get_timestamp()
            }
    
    def get_system_prompt(self) -> str:
        return """You are a chemical safety specialist. Analyze hazards, provide safety precautions, PPE recommendations, and safe handling procedures. Prioritize human safety and environmental protection. Reference safety data and provide clear, actionable recommendations."""
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
