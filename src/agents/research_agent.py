"""
Research Agent

Specialized agent for chemistry research questions, explanations, and general chemistry knowledge.
Uses ChEMBL MCP tools and PubChem for comprehensive chemical information.
"""

import re
from typing import Dict, Any, List
from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """Handles chemistry research questions and explanations"""
    
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            description="Specialized in chemistry research questions, chemical properties, and explanations",
            tools=[
                "search_compounds",
                "get_compound_info", 
                "search_targets",
                "get_target_info",
                "search_activities"
            ]
        )
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process chemistry research questions"""
        
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
        
        # First, try to get a basic OpenAI response
        try:
            conversation_history = context.get("conversation_history", []) if context else []
            openai_response = self.llm_client.generate_chat_response(enhanced_query, conversation_history)
            self.logger.info(f"Generated OpenAI response: {len(openai_response)} characters")
        except Exception as e:
            self.logger.error(f"OpenAI response failed: {e}")
            openai_response = "I'm having trouble processing your question right now."
        
        # Try to enhance with ChEMBL data (only if no PDF context to avoid duplication)
        chembl_enhancement = ""
        if not pdf_context:  # Only use ChEMBL if no PDF context
            try:
                agent_result = await self._run_agent_safely(query, context)
                
                if agent_result.get("success"):
                    # Extract ChEMBL data from agent response
                    enhancement_parts = []
                    
                    # Look for chemical data in the response
                    messages = agent_result.get("response", [])
                    for message in messages:
                        if hasattr(message, 'content') and message.content:
                            content = message.content
                            # Skip if content is too verbose (contains large JSON blocks)
                            if len(content) > 2000 or '{' in content and '"molecules"' in content:
                                self.logger.info("Skipping verbose ChEMBL response")
                                continue
                            
                            # Only add actual database results, not system prompts
                            if any(keyword in content.lower() for keyword in ["chembl", "molecular weight", "formula", "structure"]) and "system" not in content.lower():
                                # Clean up the content before adding it
                                clean_content = self._clean_chembl_content(content)
                                if clean_content and len(clean_content) < 500:  # Limit length
                                    enhancement_parts.append(clean_content)
                    
                    if enhancement_parts:
                        chembl_enhancement = "\n\nAdditional Database Information:\nDetailed chemical data retrieved from ChEMBL database.\n" + "\n".join(enhancement_parts)
                        self.logger.info(f"Added ChEMBL enhancement: {len(chembl_enhancement)} characters")
                    else:
                        self.logger.info("No ChEMBL data extracted")
                
            except Exception as e:
                self.logger.error(f"ChEMBL enhancement failed: {e}")
                chembl_enhancement = "\n\n(Note: Database access temporarily unavailable)"
        
        # Combine responses
        final_response = openai_response + chembl_enhancement
        
        return {
            "success": True,
            "response": final_response,
            "agent": self.name,
            "used_mcp": bool(chembl_enhancement),
            "timestamp": self._get_timestamp()
        }
    
    def get_system_prompt(self) -> str:
        return """You are a Research Agent specialized in chemistry research and explanations.

Your capabilities include:
- Answering chemistry questions with detailed explanations
- Providing chemical properties, structures, and formulas
- Explaining chemical reactions and mechanisms
- Accessing ChEMBL database for accurate chemical data
- Searching for compounds, targets, and bioactivity data

When answering questions:
1. Provide clear, accurate explanations
2. Use ChEMBL tools to get precise chemical data
3. Cite sources when possible
4. Explain complex concepts in understandable terms
5. Include relevant chemical properties and structures

Always prioritize accuracy and provide comprehensive information."""
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _clean_chembl_content(self, content: str) -> str:
        """Clean up ChEMBL content to extract only the essential information"""
        if not content:
            return ""
        
        # Remove verbose system prompts and capabilities
        verbose_patterns = [
            "You are a Research Agent specialized in chemistry research and explanations.",
            "Your capabilities include:",
            "- Answering chemistry questions with detailed explanations",
            "- Providing chemical properties, structures, and formulas", 
            "- Explaining chemical reactions and mechanisms",
            "- Accessing ChEMBL database for accurate chemical data",
            "- Searching for compounds, targets, and bioactivity data",
            "When answering questions:",
            "1. Provide clear, accurate explanations",
            "2. Use ChEMBL tools to get precise chemical data",
            "3. Cite sources when possible",
            "4. Explain complex concepts in understandable terms",
            "5. Include relevant chemical properties and structures",
            "Always prioritize accuracy and provide comprehensive information.",
            "ChEMBL Database:"
        ]
        
        cleaned = content
        for pattern in verbose_patterns:
            cleaned = cleaned.replace(pattern, '')
        
        # Extract key chemical information
        # Look for molecular formula
        formula_match = re.search(r'"molecular_formula":\s*"([^"]+)"', cleaned)
        if formula_match:
            formula = formula_match.group(1)
            cleaned = f"Molecular Formula: {formula}"
        
        # Look for molecular weight
        weight_match = re.search(r'"molecular_weight":\s*([0-9.]+)', cleaned)
        if weight_match:
            weight = weight_match.group(1)
            if "Molecular Formula:" in cleaned:
                cleaned += f"\nMolecular Weight: {weight} g/mol"
            else:
                cleaned = f"Molecular Weight: {weight} g/mol"
        
        # Look for canonical SMILES
        smiles_match = re.search(r'"canonical_smiles":\s*"([^"]+)"', cleaned)
        if smiles_match:
            smiles = smiles_match.group(1)
            if cleaned:
                cleaned += f"\nCanonical SMILES: {smiles}"
            else:
                cleaned = f"Canonical SMILES: {smiles}"
        
        # Clean up any remaining formatting
        cleaned = cleaned.strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Remove extra whitespace
        
        return cleaned if cleaned else ""
