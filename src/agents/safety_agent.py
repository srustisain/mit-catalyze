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
        
        try:
            # Get the main safety response
            conversation_history = context.get("conversation_history", []) if context else []
            safety_response = self.llm_client.generate_chat_response(safety_prompt, conversation_history)
            self.logger.info(f"Generated safety response: {len(safety_response)} characters")
            
            # Try to enhance with chemical safety data
            chembl_enhancement = ""
            try:
                agent_result = await self._run_agent_safely(query, context)
                
                if agent_result.get("success"):
                    # Look for chemical safety data
                    messages = agent_result.get("response", [])
                    safety_data = []
                    
                    for message in messages:
                        if hasattr(message, 'content') and message.content:
                            content = message.content
                            if any(keyword in content.lower() for keyword in ["toxic", "hazard", "safety", "risk", "flammable", "corrosive"]):
                                safety_data.append(content)
                    
                    if safety_data:
                        chembl_enhancement = "\n\n**Database Safety Information:**\n" + "\n".join(safety_data)
                        self.logger.info(f"Added safety data: {len(chembl_enhancement)} characters")
                
            except Exception as e:
                self.logger.error(f"ChEMBL enhancement failed: {e}")
                chembl_enhancement = "\n\n(Note: Safety database access temporarily unavailable)"
            
            # Combine responses
            final_response = safety_response + chembl_enhancement
            
            return {
                "success": True,
                "response": final_response,
                "agent": self.name,
                "used_mcp": bool(chembl_enhancement),
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Safety analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": self._get_timestamp()
            }
    
    def get_system_prompt(self) -> str:
        return """You are a chemical safety specialist. Analyze hazards, provide safety precautions, PPE recommendations, and safe handling procedures. Prioritize human safety and environmental protection. Reference safety data and provide clear, actionable recommendations."""
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
