"""
Automate Agent

Specialized agent for creating lab automation scripts, particularly for Opentrons and PyHamilton systems.
Generates Python code for robotic lab equipment and liquid handling systems.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from src.clients.opentrons_validator import OpentronsCodeGenerator, OpentronsValidator
from src.generators.lynx_generator import LynxCodeGenerator


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
        
        # Initialize code generators
        self.opentrons_validator = OpentronsValidator(max_retries=3)
        self.opentrons_generator = None  # Will be initialized after MCP client is ready
        self.lynx_generator = LynxCodeGenerator()
    
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
        """Generate automation scripts for lab equipment with platform selection"""
        
        try:
            # Check if this is a code generation request
            if self._is_code_generation_request(query):
                # Check if platform is already specified
                platform = self._extract_platform_from_query(query)
                
                if not platform:
                    # Ask user to choose platform
                    return self._ask_for_platform_selection(query, context)
                else:
                    # Process with specified platform
                    return await self._process_with_platform(query, context, platform)
            else:
                # Handle non-code generation requests (general automation advice, etc.)
                return await self._process_general_automation_request(query, context)
                
        except Exception as e:
            self.logger.error(f"Automation generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": self._get_timestamp()
            }
    
    def _is_code_generation_request(self, query: str) -> bool:
        """Check if the query is requesting code generation"""
        query_lower = query.lower()
        code_generation_keywords = [
            "generate code", "create code", "write code", "make code",
            "generate script", "create script", "write script", "make script",
            "generate python", "create python", "write python",
            "generate c#", "create c#", "write c#", "generate csharp", "create csharp",
            "opentrons code", "lynx code", "automation code", "protocol code",
            "code for", "script for", "python for", "c# for", "csharp for",
            "generate opentrons", "create opentrons", "write opentrons",
            "generate lynx", "create lynx", "write lynx"
        ]
        return any(keyword in query_lower for keyword in code_generation_keywords)
    
    def _extract_platform_from_query(self, query: str) -> str:
        """Extract platform preference from query"""
        query_lower = query.lower()
        
        # Check for OpenTrons references
        opentrons_keywords = ["opentrons", "ot2", "ot-2", "ot 2", "opentrons ot2"]
        if any(keyword in query_lower for keyword in opentrons_keywords):
            return "opentrons"
        
        # Check for Lynx references
        lynx_keywords = ["lynx", "dynamic device", "dynamic device lynx", "c#", "csharp"]
        if any(keyword in query_lower for keyword in lynx_keywords):
            return "lynx"
        
        return None
    
    def _ask_for_platform_selection(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ask user to choose between OpenTrons and Lynx platforms"""
        
        platform_selection_message = f"""
🤖 **Platform Selection Required**

I can generate automation code for your protocol, but I need to know which platform you'd prefer:

**1. OpenTrons OT2** - Python code for OpenTrons liquid handling robots
**2. Dynamic Device Lynx** - C# script for Lynx liquid handling systems

Please respond with:
- "OpenTrons" or "OT2" for Python code
- "Lynx" or "C#" for C# script

Your original request: {query[:200]}{'...' if len(query) > 200 else ''}
"""
        
        return {
            "success": True,
            "response": platform_selection_message,
            "agent": self.name,
            "requires_platform_selection": True,
            "original_query": query,
            "context": context,
            "timestamp": self._get_timestamp()
        }
    
    async def _process_with_platform(self, query: str, context: Dict[str, Any] = None, platform: str = None) -> Dict[str, Any]:
        """Process code generation request with specified platform"""
        
        if platform == "opentrons":
            return await self._process_opentrons_request(query, context)
        elif platform == "lynx":
            return await self._process_lynx_request(query, context)
        else:
            return {
                "success": False,
                "error": f"Unknown platform: {platform}",
                "agent": self.name,
                "timestamp": self._get_timestamp()
            }
    
    async def _process_lynx_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process Lynx-specific automation requests"""
        
        self.logger.info(f"🔧 {self.name} - Processing Lynx request: {query[:100]}...")
        print(f"🔧 {self.name} - WEBAPP DEBUG: Processing Lynx query: {query[:100]}...")
        
        # Extract protocol instructions from query and context
        instructions = self._extract_protocol_instructions(query, context)
        
        # Generate Lynx C# code
        generation_result = self.lynx_generator.generate_lynx_script(
            instructions=instructions,
            context=context
        )
        
        if generation_result["success"]:
            # Format the response with code
            response = self._format_lynx_response(generation_result)
            
            return {
                "success": True,
                "response": response,
                "agent": self.name,
                "lynx_code": generation_result.get("code"),
                "platform": "lynx",
                "language": "csharp",
                "timestamp": generation_result["timestamp"]
            }
        else:
            return {
                "success": False,
                "response": f"Lynx code generation failed: {generation_result.get('error', 'Unknown error')}",
                "agent": self.name,
                "error": generation_result.get("error", "Code generation failed"),
                "platform": "lynx",
                "timestamp": generation_result["timestamp"]
            }
    
    async def _process_general_automation_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle general automation requests that don't require code generation"""
        
        # For now, provide general automation advice
        response = f"""
🔧 **Automation Assistant**

I can help you with lab automation in several ways:

**Code Generation:**
- Ask me to "generate code" or "create a script" and I'll ask you to choose between OpenTrons (Python) or Lynx (C#)

**General Automation Advice:**
- Protocol optimization
- Equipment recommendations
- Automation best practices
- Troubleshooting automation issues

**Your Query:** {query}

Would you like me to generate code for this, or do you need general automation advice?
"""
        
        return {
            "success": True,
            "response": response,
            "agent": self.name,
            "timestamp": self._get_timestamp()
        }
    
    def _format_lynx_response(self, generation_result: Dict[str, Any]) -> str:
        """Format the Lynx generation result for display"""
        code = generation_result.get("code", "NO CODE FOUND")
        platform = generation_result.get("platform", "lynx")
        language = generation_result.get("language", "csharp")
        
        response = f"""## 🧬 Dynamic Device Lynx C# Script

Generated C# script for Lynx liquid handling system:

```csharp
{code}
```

**Platform:** {platform.title()}
**Language:** {language.upper()}
**Generated:** {generation_result.get('timestamp', 'Unknown')}

The script is ready to use with your Lynx system. Make sure to adjust the plate locations and parameters according to your specific setup.
"""
        
        return response
    
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
