"""
Automate Agent

Specialized agent for creating lab automation scripts, particularly for Opentrons and PyHamilton systems.
Generates Python code for robotic lab equipment and liquid handling systems.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from src.clients.opentrons_validator import OpentronsCodeGenerator, OpentronsValidator

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
        
        # Initialize Opentrons code generator with validation
        self.opentrons_validator = OpentronsValidator(max_retries=3)
        self.opentrons_generator = None  # Will be initialized after MCP client is ready
    
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
                "opentrons_code": generation_result["code"],
                "validation_result": generation_result["validation_result"],
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
