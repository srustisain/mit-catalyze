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
            # All automate agent requests go through Opentrons generator/validator
            self.logger.info(f"🔧 {self.name} - Processing Opentrons request: {query[:100]}...")
            print(f"🔧 {self.name} - WEBAPP DEBUG: Processing query: {query[:100]}...")
            result = await self._process_opentrons_request(query, context)
            print(f"🔧 {self.name} - WEBAPP DEBUG: Result keys: {list(result.keys())}")
            if 'opentrons_code' in result:
                print(f"🔧 {self.name} - WEBAPP DEBUG: Opentrons code length: {len(result['opentrons_code']) if result['opentrons_code'] else 'None'}")
            return result
                
        except Exception as e:
            self.logger.error(f"Automation generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": self._get_timestamp()
            }
    
    
    async def _process_opentrons_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process Opentrons-specific automation requests with validation"""
        
        # Ensure Opentrons generator is initialized
        await self._ensure_opentrons_generator()
        
        # Extract protocol instructions from query and context
        instructions = self._extract_protocol_instructions(query, context)
        
        self.logger.info(f"🔧 {self.name} - Processing Opentrons request: {instructions[:100]}...")
        
        # Log MCP tool usage
        if self.mcp_client:
            self.logger.info(f"🔧 {self.name} - MCP client available, will use Opentrons documentation")
        else:
            self.logger.warning(f"🔧 {self.name} - MCP client not available, using fallback generation")
        
        # Generate Opentrons code with validation
        generation_result = await self.opentrons_generator.generate_with_validation(
            instructions=instructions,
            context=context,
            max_retries=3
        )
        
        if generation_result["success"]:
            # Format the response with code and validation info
            response = self._format_opentrons_response(generation_result)
            print("---------------", response, "---------------------------")
            
            return {
                "success": True,
                "response": response,
                "agent": self.name,
                "opentrons_code": generation_result.get("code"),  # Use "code" key, not "opentrons_code"
                "validation_result": generation_result.get("validation_result"),
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
        code = generation_result.get("code", "NO CODE FOUND")
        validation_result = generation_result.get("validation_result")
        attempts = generation_result["attempts"]
        
        response = code
        
        if validation_result.warnings:
            response += f"**Warnings:**\n{chr(10).join([f'- {w}' for w in validation_result.warnings])}\n\n"
        
        # response += "The protocol has been validated using Opentrons simulation and is ready to use."
        
        return response
    
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
