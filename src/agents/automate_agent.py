"""
Automate Agent

Specialized agent for creating lab automation scripts, particularly for Opentrons and PyHamilton systems.
Generates Python code for robotic lab equipment and liquid handling systems.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from src.clients.opentrons_validator import OpentronsCodeGenerator, OpentronsValidator
from src.generators.lynx_generator import LynxCodeGenerator

# Try to import Langfuse decorator
try:
    from langfuse.decorators import observe
except ImportError:
    # Create a no-op decorator if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])


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
        """Ensure Opentrons generator is initialized with MCP client and LLM"""
        if self.opentrons_generator is None:
            if self.mcp_client:
                self.opentrons_generator = OpentronsCodeGenerator(
                    validator=self.opentrons_validator,
                    mcp_client=self.mcp_client,
                    llm_client=self.llm_client  # Pass LLM client for code generation
                )
            else:
                # Fallback without MCP client
                self.opentrons_generator = OpentronsCodeGenerator(
                    validator=self.opentrons_validator,
                    mcp_client=None,
                    llm_client=self.llm_client  # Still pass LLM client
                )
    
    @observe()
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
        """Process Opentrons-specific automation requests with LangGraph agent and validation"""
        
        # Ensure Opentrons generator is initialized for validation
        await self._ensure_opentrons_generator()
        
        # Extract protocol instructions from query and context
        instructions = self._extract_protocol_instructions(query, context)
        
        # Extract specific details from conversation context to make code generation less generic
        equipment_details = self._extract_equipment_details(context)
        volume_details = self._extract_volume_details(query, context)
        labware_details = self._extract_labware_details(query, context)
        conversation_context = self._format_conversation_context(context)
        
        self.logger.info(f"Processing Opentrons request with LangGraph agent: {instructions[:100]}...")
        self.logger.info(f"Context: Equipment={equipment_details}, Volumes={volume_details}, Labware={labware_details}")
        
        # Use LangGraph agent to generate code (with MCP tools)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Create context-aware prompt for Opentrons code generation
                generation_prompt = f"""
Generate a complete Opentrons Python protocol for the following instructions:

{instructions}

SPECIFIC REQUIREMENTS FROM CONTEXT:
- Equipment: {equipment_details}
- Volumes: {volume_details}
- Labware: {labware_details}

PREVIOUS CONVERSATION CONTEXT:
{conversation_context}

Use the Opentrons MCP documentation tools to find:
1. Exact labware names and specifications matching the requirements above
2. Pipette models and their volume ranges appropriate for the specified volumes
3. Best practices for the specific protocol type

Requirements:
1. Use Opentrons API version 2.13
2. Include proper metadata (protocolName, author, description, apiLevel)
3. Load SPECIFIC labware mentioned in context or appropriate for the task
4. Use SPECIFIC volumes and concentrations mentioned above
5. Implement the EXACT protocol steps described
6. Add detailed comments explaining each step
7. Include error handling and validation
8. Make the code ready for simulation and execution

IMPORTANT:
- Use exact details from the conversation (volumes, concentrations, equipment)
- Query Opentrons documentation for correct labware names using available tools
- Generate ONLY Python code, starting with imports
- Do not use placeholder values - use actual values from context
- Do not include explanations or markdown formatting
"""
                
                # Use LangGraph agent with Opentrons MCP tools
                if self.agent and self.mcp_client:
                    agent_result = await self._run_agent_safely(generation_prompt, context)
                    
                    if agent_result.get("success"):
                        generated_code = agent_result.get("response", "")
                        
                        # Extract code if wrapped in markdown
                        if "```python" in generated_code:
                            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
                        elif "```" in generated_code:
                            generated_code = generated_code.split("```")[1].split("```")[0].strip()
                        
                        self.logger.info(f"LangGraph agent generated code (attempt {attempt + 1})")
                        
                        # Validate the generated code
                        validation_result = await self.opentrons_validator.validate_code(generated_code)
                        
                        if validation_result.success:
                            # Success! Return the validated code
                            response = self._format_opentrons_response({
                                "code": generated_code,
                                "validation_result": validation_result,
                                "attempts": attempt + 1,
                                "timestamp": self._get_timestamp()
                            })
                            
                            return {
                                "success": True,
                                "response": response,
                                "agent": self.name,
                                "opentrons_code": generated_code,
                                "validation_result": validation_result,
                                "attempts": attempt + 1,
                                "used_langgraph": True,
                                "timestamp": self._get_timestamp()
                            }
                        else:
                            # Validation failed, retry with error feedback
                            self.logger.warning(f"Validation failed (attempt {attempt + 1}): {validation_result.errors}")
                            
                            if attempt < max_retries - 1:
                                # Add error feedback for next attempt
                                error_summary = "\n".join([f"- {err}" for err in validation_result.errors])
                                suggestions_summary = "\n".join([f"- {sug}" for sug in validation_result.suggestions])
                                
                                instructions = f"""
{instructions}

PREVIOUS ATTEMPT HAD ERRORS:
{error_summary}

SUGGESTIONS FOR IMPROVEMENT:
{suggestions_summary}

Please generate the code again with these issues fixed.
"""
                                continue
                            else:
                                # Max retries exceeded
                                error_response = f"""
Opentrons code generation failed after {attempt + 1} attempts using LangGraph agent.

Errors encountered:
{chr(10).join([f'- {error}' for error in validation_result.errors])}

Suggestions:
{chr(10).join([f'- {suggestion}' for suggestion in validation_result.suggestions])}
"""
                                return {
                                    "success": False,
                                    "response": error_response,
                                    "agent": self.name,
                                    "error": "Validation failed after max retries",
                                    "attempts": attempt + 1,
                                    "timestamp": self._get_timestamp()
                                }
                    else:
                        # Agent failed, try next attempt
                        self.logger.warning(f"Agent failed (attempt {attempt + 1}): {agent_result.get('error')}")
                        if attempt >= max_retries - 1:
                            return await self._fallback_opentrons_generation(instructions, context)
                        continue
                else:
                    # No LangGraph agent available, use fallback
                    self.logger.warning("LangGraph agent not available, using fallback")
                    return await self._fallback_opentrons_generation(instructions, context)
                    
            except Exception as e:
                self.logger.error(f"Opentrons generation attempt {attempt + 1} failed: {e}")
                if attempt >= max_retries - 1:
                    return {
                        "success": False,
                        "response": f"Code generation failed: {str(e)}",
                        "agent": self.name,
                        "error": str(e),
                        "attempts": attempt + 1,
                        "timestamp": self._get_timestamp()
                    }
        
        # Should not reach here
        return await self._fallback_opentrons_generation(instructions, context)
    
    async def _fallback_opentrons_generation(self, instructions: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback to template-based generation when LangGraph agent fails"""
        self.logger.info("Using fallback template-based Opentrons generation")
        
        # Use the original OpentronsCodeGenerator as fallback
        generation_result = await self.opentrons_generator.generate_with_validation(
            instructions=instructions,
            context=context,
            max_retries=2
        )
        
        if generation_result["success"]:
            response = self._format_opentrons_response(generation_result)
            return {
                "success": True,
                "response": response,
                "agent": self.name,
                "opentrons_code": generation_result.get("code"),  # Use "code" key, not "opentrons_code"
                "validation_result": generation_result.get("validation_result"),
                "attempts": generation_result["attempts"],
                "used_fallback": True,
                "timestamp": generation_result["timestamp"]
            }
        else:
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
                    # Response is already extracted as string from _run_agent_safely
                    response_content = agent_result.get("response", "")
                    
                    # Look for chemical data that could inform automation parameters
                    if response_content and any(keyword in response_content.lower() for keyword in ["molecular weight", "concentration", "volume", "properties"]):
                        chembl_enhancement = "\n\n**Chemical Parameters for Automation:**\n" + response_content
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
    
    def _extract_equipment_details(self, context: Dict[str, Any]) -> str:
        """Extract equipment specifications from conversation context"""
        import re
        
        if not context or not context.get("conversation_history"):
            return "Standard Opentrons OT-2"
        
        # Keywords for equipment types
        equipment_keywords = {
            "OT-2": ["ot-2", "ot2", "opentrons 2"],
            "Flex": ["flex", "opentrons flex"],
            "pipettes": ["p20", "p300", "p1000", "pipette", "single channel", "multi channel"]
        }
        
        found_equipment = []
        for msg in context["conversation_history"][-5:]:
            content = msg.get("content", "").lower()
            
            for equip_type, keywords in equipment_keywords.items():
                if any(kw in content for kw in keywords):
                    # Extract the specific mention
                    for kw in keywords:
                        if kw in content:
                            found_equipment.append(kw.upper())
                            break
        
        return ", ".join(set(found_equipment)) if found_equipment else "Standard Opentrons OT-2"
    
    def _extract_volume_details(self, query: str, context: Dict[str, Any]) -> str:
        """Extract volume requirements from query and conversation context"""
        import re
        
        # Pattern to match volumes: number + unit (µL, mL, L, uL)
        volume_pattern = r'(\d+\.?\d*)\s*(µL|uL|mL|ml|L|ul|μL)'
        
        volumes = []
        
        # Check query
        found = re.findall(volume_pattern, query, re.IGNORECASE)
        volumes.extend([f"{num} {unit}" for num, unit in found])
        
        # Check conversation history
        if context and context.get("conversation_history"):
            for msg in context["conversation_history"][-3:]:
                content = msg.get("content", "")
                found = re.findall(volume_pattern, content, re.IGNORECASE)
                volumes.extend([f"{num} {unit}" for num, unit in found])
        
        return ", ".join(set(volumes)) if volumes else "Standard volumes as appropriate"
    
    def _extract_labware_details(self, query: str, context: Dict[str, Any]) -> str:
        """Extract labware specifications from query and conversation"""
        import re
        
        # Common Opentrons labware keywords
        labware_keywords = [
            "96.*well", "384.*well", "24.*well", "6.*well",
            "plate", "tube rack", "reservoir", "tip rack",
            "pcr", "deep.*well", "falcon", "eppendorf"
        ]
        
        found_labware = []
        
        # Check query
        for pattern in labware_keywords:
            matches = re.findall(pattern, query, re.IGNORECASE)
            found_labware.extend(matches)
        
        # Check conversation history
        if context and context.get("conversation_history"):
            for msg in context["conversation_history"][-3:]:
                content = msg.get("content", "")
                for pattern in labware_keywords:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    found_labware.extend(matches)
        
        return ", ".join(set(found_labware)) if found_labware else "Standard labware"
    
    def _format_conversation_context(self, context: Dict[str, Any]) -> str:
        """Format recent conversation for context in prompts"""
        if not context or not context.get("conversation_history"):
            return "No previous context"
        
        history = context["conversation_history"][-5:]  # Last 5 messages
        formatted = []
        
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # Truncate long messages
            if len(content) > 200:
                content = content[:200] + "..."
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted)
    
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
