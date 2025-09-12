"""
Protocol Agent

Specialized agent for generating lab protocols, experimental procedures, and step-by-step methods.
Focuses on creating detailed, safe, and reproducible laboratory procedures.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class ProtocolAgent(BaseAgent):
    """Generates lab protocols and experimental procedures"""
    
    def __init__(self):
        super().__init__(
            name="ProtocolAgent",
            description="Specialized in generating lab protocols, experimental procedures, and methods",
            tools=[
                "search_compounds",
                "get_compound_info",
                "search_activities", 
                "get_assay_info",
                "search_drugs"
            ]
        )
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate lab protocols and procedures"""
        
        # Check for PDF context
        pdf_context = context.get("pdf_context") if context else None
        pdf_info = ""
        
        if pdf_context:
            pdf_info = f"""
            
            **PDF Document Context:**
            You are also referencing a scientific PDF document titled "{pdf_context.get('filename', 'Unknown')}".
            The document contains the following relevant information:
            
            {pdf_context.get('content', '')}
            
            Please incorporate relevant methodologies, protocols, or procedures from this document into your protocol generation.
            Reference specific experimental details or safety measures from the PDF when applicable.
            """
        
        # Create a protocol-focused prompt
        protocol_prompt = f"""
Generate a detailed lab protocol for: {query}

Include:
1. Objective/Purpose
2. Materials and Equipment
3. Safety Precautions
4. Step-by-step Procedure
5. Expected Results
6. Troubleshooting Tips
7. References

Make it detailed, safe, and reproducible for laboratory use.
{pdf_info}
"""
        
        try:
            # Get the main protocol response
            conversation_history = context.get("conversation_history", []) if context else []
            protocol_response = self.llm_client.generate_chat_response(protocol_prompt, conversation_history)
            self.logger.info(f"Generated protocol response: {len(protocol_response)} characters")
            
            # Try to enhance with ChEMBL data for chemical information
            chembl_enhancement = ""
            try:
                agent_result = await self._run_agent_safely(query, context)
                
                if agent_result.get("success"):
                    # Look for chemical data that could enhance the protocol
                    messages = agent_result.get("response", [])
                    chemical_data = []
                    
                    for message in messages:
                        if hasattr(message, 'content') and message.content:
                            content = message.content
                            if any(keyword in content.lower() for keyword in ["molecular weight", "formula", "structure", "properties"]):
                                chemical_data.append(content)
                    
                    if chemical_data:
                        chembl_enhancement = "\n\n**Chemical Data for Protocol:**\n" + "\n".join(chemical_data)
                        self.logger.info(f"Added chemical data: {len(chembl_enhancement)} characters")
                
            except Exception as e:
                self.logger.error(f"ChEMBL enhancement failed: {e}")
                chembl_enhancement = "\n\n(Note: Chemical database access temporarily unavailable)"
            
            # Combine responses
            final_response = protocol_response + chembl_enhancement
            
            # Store protocol for automation
            protocol_data = {
                "protocol_text": final_response,
                "timestamp": self._get_timestamp()
            }
            
            return {
                "success": True,
                "response": final_response,
                "agent": self.name,
                "used_mcp": bool(chembl_enhancement),
                "protocol_data": protocol_data,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Protocol generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": self._get_timestamp()
            }
    
    def get_system_prompt(self) -> str:
        return """You are a laboratory protocol specialist. Generate detailed, step-by-step lab procedures for synthesis, analysis, and experiments. Always include safety precautions, materials, quantities, temperatures, and timing. Make protocols clear, safe, and reproducible."""
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
