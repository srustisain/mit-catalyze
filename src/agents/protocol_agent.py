"""
Protocol Agent

Specialized agent for generating lab protocols, experimental procedures, and step-by-step methods.
Focuses on creating detailed, safe, and reproducible laboratory procedures.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent

# Try to import Langfuse decorator
try:
    from langfuse.decorators import observe
except ImportError:
    # Create a no-op decorator if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])


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
    
    @observe()
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
        
        # Use the LangGraph agent with MCP tools directly
        if self.agent and self.mcp_client:
            try:
                # Let the LangGraph agent handle the query with MCP tools
                agent_result = await self._run_agent_safely(protocol_prompt, context)
                
                if agent_result.get("success"):
                    # Response is already extracted as string from _run_agent_safely
                    response_content = agent_result.get("response", "")
                    
                    # Store protocol for automation
                    protocol_data = {
                        "protocol_text": response_content,
                        "timestamp": self._get_timestamp()
                    }
                    
                    return {
                        "success": True,
                        "response": response_content,
                        "agent": self.name,
                        "used_mcp": True,
                        "protocol_data": protocol_data,
                        "timestamp": self._get_timestamp()
                    }
                else:
                    # Fallback to basic LLM response
                    return await self._fallback_response(protocol_prompt, context)
                    
            except Exception as e:
                self.logger.error(f"LangGraph agent failed: {e}")
                return await self._fallback_response(protocol_prompt, context)
        else:
            # Fallback to basic LLM response if no agent available
            return await self._fallback_response(protocol_prompt, context)
    
    async def _fallback_response(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback response when MCP tools are not available"""
        try:
            conversation_history = context.get("conversation_history", []) if context else []
            response = self.llm_client.generate_chat_response(query, conversation_history)
            self.logger.info(f"Generated fallback protocol response: {len(response)} characters")
            
            # Store protocol for automation
            protocol_data = {
                "protocol_text": response,
                "timestamp": self._get_timestamp()
            }
            
            return {
                "success": True,
                "response": response,
                "agent": self.name,
                "used_mcp": False,
                "protocol_data": protocol_data,
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            self.logger.error(f"Fallback response failed: {e}")
            return {
                "success": False,
                "response": "I'm having trouble generating the protocol right now.",
                "agent": self.name,
                "used_mcp": False,
                "timestamp": self._get_timestamp()
            }
    
    def get_system_prompt(self) -> str:
        return """You are a laboratory protocol specialist. Generate detailed, step-by-step lab procedures for synthesis, analysis, and experiments. Always include safety precautions, materials, quantities, temperatures, and timing. Make protocols clear, safe, and reproducible."""
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
