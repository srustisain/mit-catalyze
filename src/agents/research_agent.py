"""
Research Agent

Specialized agent for chemistry research questions, explanations, and general chemistry knowledge.
Uses ChEMBL MCP tools and PubChem for comprehensive chemical information.
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


class ResearchAgent(BaseAgent):
    """Handles chemistry research questions and explanations"""
    
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            description="Specialized in chemistry research questions, chemical properties, and explanations",
            tools=None  # Use all available ChEMBL tools
        )
    
    @observe()
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process chemistry research questions"""
        
        if context is None:
            context = {}
        
        # Check for PDF context
        pdf_context = context.get("pdf_context") if context else None
        enhanced_query = query
        
        if pdf_context:
            enhanced_query = f"""
            Research Question: {query}
            
            CONTEXT: You are analyzing a scientific PDF document titled "{pdf_context.get('filename', 'Unknown')}".
            
            DOCUMENT CONTENT:
            {pdf_context.get('content', '')}
            
            INSTRUCTIONS:
            - Answer the research question using information from the PDF document
            - Reference specific findings, data, methods, or conclusions from the document
            - If the question relates to content in the PDF, provide detailed explanations based on the document
            - If the question is not directly addressed in the PDF, mention this and provide general information
            - Always cite specific sections, findings, or data from the PDF when relevant
            """
            self.logger.info(f"Enhanced query with PDF context from: {pdf_context.get('filename', 'Unknown')}")
        
        # Use the LangGraph agent with MCP tools directly
        if self.agent and self.mcp_client:
            try:
                # Let the LangGraph agent handle the query with MCP tools
                agent_result = await self._run_agent_safely(enhanced_query, context)
                
                if agent_result.get("success"):
                    # Response is already extracted as string from _run_agent_safely
                    response_content = agent_result.get("response", "")
                    
                    return {
                        "success": True,
                        "response": response_content,
                        "agent": self.name,
                        "used_mcp": True,
                        "timestamp": self._get_timestamp()
                    }
                else:
                    # Fallback to basic LLM response
                    return await self._fallback_response(enhanced_query, context)
                    
            except Exception as e:
                self.logger.error(f"LangGraph agent failed: {e}")
                return await self._fallback_response(enhanced_query, context)
        else:
            # Fallback to basic LLM response if no agent available
            return await self._fallback_response(enhanced_query, context)
    
    async def _fallback_response(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback response with direct MCP tool usage"""
        try:
            # Try to use MCP tools directly if available
            mcp_enhancement = ""
            if self.mcp_client:
                try:
                    # Use a simple compound search for chemical queries
                    if any(keyword in query.lower() for keyword in ["molecular weight", "formula", "structure", "compound", "chemical"]):
                        tools = await self.mcp_client.get_tools()
                        search_tool = next((tool for tool in tools if tool.name == "search_compounds"), None)
                        
                        if search_tool:
                            # Extract compound name from query
                            compound_name = self._extract_compound_name(query)
                            if compound_name:
                                result = await search_tool.ainvoke({"query": compound_name, "limit": 3})
                                if result and "molecules" in result:
                                    mcp_enhancement = f"\n\n**Database Information:**\n{self._format_compound_data(result)}"
                                    self.logger.info(f"Added MCP data: {len(mcp_enhancement)} characters")
                except Exception as e:
                    self.logger.warning(f"MCP tool usage failed: {e}")
            
            # Generate base response
            conversation_history = context.get("conversation_history", []) if context else []
            base_response = self.llm_client.generate_chat_response(query, conversation_history)
            
            # Combine with MCP data
            final_response = base_response + mcp_enhancement
            
            self.logger.info(f"Generated fallback response: {len(final_response)} characters")
            
            return {
                "success": True,
                "response": final_response,
                "agent": self.name,
                "used_mcp": bool(mcp_enhancement),
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            self.logger.error(f"Fallback response failed: {e}")
            return {
                "success": False,
                "response": "I'm having trouble processing your question right now.",
                "agent": self.name,
                "used_mcp": False,
                "timestamp": self._get_timestamp()
            }
    
    def _extract_compound_name(self, query: str) -> str:
        """Extract compound name from query"""
        # Simple extraction - look for common patterns
        query_lower = query.lower()
        
        # Look for "molecular weight of X" pattern
        if "molecular weight of" in query_lower:
            return query.split("molecular weight of")[-1].strip().rstrip("?")
        
        # Look for "what is X" pattern
        if "what is" in query_lower and any(chem in query_lower for chem in ["aspirin", "caffeine", "compound", "chemical"]):
            parts = query.split("what is")
            if len(parts) > 1:
                return parts[1].strip().rstrip("?")
        
        return ""
    
    def _format_compound_data(self, data: Dict[str, Any]) -> str:
        """Format compound data from MCP response"""
        if not data or "molecules" not in data:
            return ""
        
        molecules = data["molecules"]
        if not molecules:
            return "No compound data found."
        
        result = []
        for mol in molecules[:2]:  # Limit to 2 results
            name = mol.get("pref_name", "Unknown")
            mw = mol.get("molecule_properties", {}).get("molecular_weight")
            smiles = mol.get("molecule_structures", {}).get("canonical_smiles", "")
            
            info = f"• {name}"
            if mw:
                info += f" (MW: {mw} g/mol)"
            if smiles:
                info += f" [SMILES: {smiles}]"
            
            result.append(info)
        
        return "\n".join(result)
    
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
