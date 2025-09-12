"""
Automate Agent

Specialized agent for creating lab automation scripts, particularly for Opentrons and PyHamilton systems.
Generates Python code for robotic lab equipment and liquid handling systems.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class AutomateAgent(BaseAgent):
    """Creates automation scripts for lab equipment"""
    
    def __init__(self):
        super().__init__(
            name="AutomateAgent",
            description="Specialized in creating lab automation scripts for robotic systems",
            tools=[
                "search_compounds",
                "get_compound_info",
                "search_activities",
                "get_assay_info", 
                "search_drugs"
            ]
        )
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate automation scripts for lab equipment"""
        
        # Create an automation-focused prompt
        automation_prompt = f"""
Create a lab automation script for: {query}

Generate Python code for lab automation equipment (Opentrons, PyHamilton, etc.).

Include:
1. Import statements for required libraries
2. Protocol definition and setup
3. Liquid handling instructions
4. Temperature and timing controls
5. Error handling and safety checks
6. Comments explaining each step

Make the code production-ready and well-documented.
"""
        
        try:
            # Get the main automation response
            conversation_history = context.get("conversation_history", []) if context else []
            automation_response = self.llm_client.generate_chat_response(automation_prompt, conversation_history)
            self.logger.info(f"Generated automation response: {len(automation_response)} characters")
            
            # Try to enhance with chemical data for accurate volumes/concentrations
            chembl_enhancement = ""
            try:
                agent_result = await self._run_agent_safely(query, context)
                
                if agent_result.get("success"):
                    # Look for chemical data that could inform automation parameters
                    messages = agent_result.get("response", [])
                    chemical_data = []
                    
                    for message in messages:
                        if hasattr(message, 'content') and message.content:
                            content = message.content
                            if any(keyword in content.lower() for keyword in ["molecular weight", "concentration", "volume", "properties"]):
                                chemical_data.append(content)
                    
                    if chemical_data:
                        chembl_enhancement = "\n\n**Chemical Parameters for Automation:**\n" + "\n".join(chemical_data)
                        self.logger.info(f"Added chemical parameters: {len(chembl_enhancement)} characters")
                
            except Exception as e:
                self.logger.error(f"ChEMBL enhancement failed: {e}")
                chembl_enhancement = "\n\n(Note: Chemical database access temporarily unavailable)"
            
            # Combine responses
            final_response = automation_response + chembl_enhancement
            
            return {
                "success": True,
                "response": final_response,
                "agent": self.name,
                "used_mcp": bool(chembl_enhancement),
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Automation generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": self._get_timestamp()
            }
    
    def get_system_prompt(self) -> str:
        return """You are an Automate Agent specialized in creating lab automation scripts.

Your capabilities include:
- Generating Python code for Opentrons liquid handling robots
- Creating PyHamilton automation scripts
- Writing protocols for robotic lab equipment
- Designing automated experimental workflows
- Accessing chemical databases for accurate parameters

When creating automation scripts:
1. Use proper Python syntax and best practices
2. Include comprehensive error handling
3. Add detailed comments explaining each step
4. Consider safety and validation checks
5. Optimize for efficiency and reliability
6. Include proper import statements
7. Use accurate chemical parameters from databases

Focus on creating production-ready, safe, and efficient automation code."""
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
