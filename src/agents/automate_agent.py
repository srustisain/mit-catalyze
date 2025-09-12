"""
Automate Agent

Specialized agent for creating lab automation scripts, particularly for Opentrons and PyHamilton systems.
Generates Python code for robotic lab equipment and liquid handling systems.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from src.clients.opentrons_validator import OpentronsCodeGenerator, OpentronsValidator


class AutomateAgent(BaseAgent):
    """Creates automation scripts for lab equipment"""
    
    def __init__(self):
        super().__init__(
            name="AutomateAgent",
            description="Specialized in creating lab automation scripts for robotic systems",
            tools=[
                "fetch_general",
                "list_documents",
                "search_document"
            ]
        )
        
        # Initialize Opentrons code generator with validation
        self.opentrons_validator = OpentronsValidator(max_retries=3)
        self.opentrons_generator = None  # Will be initialized after MCP client is ready
    
    async def _ensure_opentrons_generator(self):
        """Ensure Opentrons generator is initialized with MCP client"""
        if self.opentrons_generator is None:
            if self.mcp_client:
                self.opentrons_generator = OpentronsCodeGenerator(
                    validator=self.opentrons_validator,
                    mcp_client=self.mcp_client
                )
            else:
                # Fallback without MCP client
                self.opentrons_generator = OpentronsCodeGenerator(
                    validator=self.opentrons_validator,
                    mcp_client=None
                )
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate automation scripts for lab equipment with Opentrons validation"""
        
        try:
            # Check if this is an Opentrons-specific request
            if self._is_opentrons_request(query):
                return await self._process_opentrons_request(query, context)
            else:
                return await self._process_general_automation(query, context)
                
        except Exception as e:
            self.logger.error(f"Automation generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": self._get_timestamp()
            }
    
    def _is_opentrons_request(self, query: str) -> bool:
        """Check if the query is specifically for Opentrons automation"""
        opentrons_keywords = [
            "opentrons", "ot-2", "ot2", "flex", "protocol", "pipette", "liquid handling",
            "write code", "generate code", "create code", "code for", "script for",
            "automation", "robot", "robotic", "lab automation", "liquid handling robot"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in opentrons_keywords)
    
    async def _process_opentrons_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process Opentrons-specific automation requests with validation"""
        
        # Ensure Opentrons generator is initialized
        await self._ensure_opentrons_generator()
        
        # Extract protocol instructions from query and context
        instructions = self._extract_protocol_instructions(query, context)
        
        self.logger.info(f"Processing Opentrons request: {instructions[:100]}...")
        
        # Generate Opentrons code with validation
        generation_result = await self.opentrons_generator.generate_with_validation(
            instructions=instructions,
            context=context,
            max_retries=3
        )
        
        if generation_result["success"]:
            # Format the response with code and validation info
            response = self._format_opentrons_response(generation_result)
            
            return {
                "success": True,
                "response": response,
                "agent": self.name,
                "opentrons_code": generation_result["code"],
                "validation_result": generation_result["validation_result"],
                "attempts": generation_result["attempts"],
                "timestamp": generation_result["timestamp"]
            }
        else:
            # Return error information
            validation_result = generation_result.get('validation_result')
            errors = validation_result.errors if validation_result else ['Unknown error']
            suggestions = validation_result.suggestions if validation_result else ['Please review the request and try again']
            
            error_response = f"""
Opentrons code generation failed after {generation_result['attempts']} attempts.

Errors encountered:
{chr(10).join([f'- {error}' for error in errors])}

Suggestions:
{chr(10).join([f'- {suggestion}' for suggestion in suggestions])}
"""
            
            return {
                "success": False,
                "response": error_response,
                "agent": self.name,
                "error": generation_result.get("error", "Code generation failed"),
                "attempts": generation_result["attempts"],
                "timestamp": generation_result["timestamp"]
            }
    
    async def _process_general_automation(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process general automation requests (non-Opentrons)"""
        
        # Create an automation-focused prompt
        automation_prompt = f"""
Create a lab automation script for: {query}

Generate Python code for lab automation equipment (PyHamilton, etc.).

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
            self.logger.error(f"General automation generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": self._get_timestamp()
            }
    
    def _extract_protocol_instructions(self, query: str, context: Dict[str, Any] = None) -> str:
        """Extract protocol instructions from query and context"""
        instructions = query
        
        # Add context from previous conversation or protocol data
        if context:
            if "protocol_data" in context:
                instructions += f"\n\nProtocol context: {context['protocol_data']}"
            
            if "conversation_history" in context:
                # Add relevant context from conversation
                recent_messages = context["conversation_history"][-3:]  # Last 3 messages
                context_text = "\n".join([msg.get("content", "") for msg in recent_messages if msg.get("content")])
                if context_text:
                    instructions += f"\n\nConversation context: {context_text}"
        
        return instructions
    
    def _format_opentrons_response(self, generation_result: Dict[str, Any]) -> str:
        """Format the Opentrons generation result for display"""
        code = generation_result["code"]
        validation_result = generation_result["validation_result"]
        attempts = generation_result["attempts"]
        
        response = f"""🤖 **Opentrons Protocol Generated Successfully**

Generated in {attempts} attempt(s) with validation.

```python
{code}
```

**Validation Status:** ✅ Passed
**Simulation Time:** {validation_result.simulation_time:.2f}s

"""
        
        if validation_result.warnings:
            response += f"**Warnings:**\n{chr(10).join([f'- {w}' for w in validation_result.warnings])}\n\n"
        
        response += "The protocol has been validated using Opentrons simulation and is ready to use."
        
        return response
    
    def get_system_prompt(self) -> str:
        return """You are a lab automation specialist. Use opentrons docs tools available via the mcp server. Generate Python code for Opentrons robots and other lab automation equipment. Create production-ready scripts with proper error handling, safety checks, and detailed comments. Use accurate chemical parameters and optimize for efficiency."""
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
