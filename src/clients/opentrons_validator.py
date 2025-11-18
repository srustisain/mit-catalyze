"""
Opentrons Code Validator

Validates Opentrons protocol code using the opentrons.simulate package.
Provides detailed error analysis and improvement suggestions for code regeneration.
"""

import tempfile
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    from opentrons.simulate import simulate, format_runlog
    OPENTRONS_AVAILABLE = True
except ImportError:
    OPENTRONS_AVAILABLE = False
    logging.warning("Opentrons package not available. Simulation validation will be disabled.")

# Langfuse integration for tracing
try:
    from langfuse.decorators import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    # No-op decorator if Langfuse not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])
    LANGFUSE_AVAILABLE = False


@dataclass
class ValidationResult:
    """Result of Opentrons code validation"""
    success: bool
    errors: List[str]
    warnings: List[str]
    runlog: Optional[str] = None
    suggestions: List[str] = None
    simulation_time: Optional[float] = None


class OpentronsValidator:
    """Validates Opentrons protocol code using simulation"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.logger = logging.getLogger("catalyze.opentrons_validator")
        
        if not OPENTRONS_AVAILABLE:
            self.logger.warning("Opentrons package not available. Validation will be disabled.")
    
    def _validate_deck_slots(self, code: str, platform: str = "ot2") -> Tuple[List[str], List[str]]:
        """
        Pre-validate deck slot names in the code before simulation
        
        Args:
            code: Python code to validate
            platform: 'ot2' or 'flex'
            
        Returns:
            Tuple of (errors, warnings) lists
        """
        import re
        
        errors = []
        warnings = []
        
        # Define valid slots for each platform
        if platform == "ot2":
            valid_slots = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'}
            invalid_pattern = r"load_labware\([^,]+,\s*['\"]([A-Z]\d+)['\"]"  # Flex-style slots
        else:  # flex
            valid_slots = {'A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'D3'}
            invalid_pattern = r"load_labware\([^,]+,\s*['\"](\d+)['\"]"  # OT-2 style slots
        
        # Find all load_labware calls
        load_pattern = r"load_labware\([^,]+,\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(load_pattern, code)
        
        for slot in matches:
            if slot not in valid_slots:
                if platform == "ot2":
                    errors.append(f"Invalid deck slot '{slot}' for OT-2. Valid slots are: {', '.join(sorted(valid_slots, key=lambda x: int(x)))}")
                else:
                    errors.append(f"Invalid deck slot '{slot}' for Flex. Valid slots are: {', '.join(sorted(valid_slots))}")
        
        # Check for wrong platform slots
        wrong_platform_matches = re.findall(invalid_pattern, code)
        if wrong_platform_matches:
            if platform == "ot2":
                errors.append(f"Found Flex-style coordinate slots ({', '.join(wrong_platform_matches)}) in OT-2 code. Use numeric slots 1-11.")
            else:
                errors.append(f"Found OT-2 style numeric slots ({', '.join(wrong_platform_matches)}) in Flex code. Use coordinate slots A1-D3.")
        
        return errors, warnings
    
    @observe(as_type="span", name="opentrons_validation")
    async def validate_code(self, code: str, platform: str = "ot2") -> ValidationResult:
        """
        Validate Opentrons protocol code using simulation with Langfuse tracing
        
        Args:
            code: Python code containing Opentrons protocol
            platform: 'ot2' or 'flex' - the target Opentrons platform
            
        Returns:
            ValidationResult with validation status and details
        """
        if not OPENTRONS_AVAILABLE:
            return ValidationResult(
                success=False,
                errors=["Opentrons package not available"],
                warnings=[],
                suggestions=["Install opentrons package: pip install opentrons"]
            )
        
        start_time = datetime.now()
        
        # Pre-validate deck slots before simulation
        slot_errors, slot_warnings = self._validate_deck_slots(code, platform)
        if slot_errors:
            self.logger.error(f"Deck slot validation failed: {slot_errors}")
            return ValidationResult(
                success=False,
                errors=slot_errors,
                warnings=slot_warnings,
                suggestions=[
                    f"Use correct deck slot naming for {platform.upper()}",
                    "Check all load_labware() calls for proper slot format"
                ],
                simulation_time=(datetime.now() - start_time).total_seconds()
            )
        
        try:
            # Create temporary file for the protocol
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Read and simulate the protocol
                with open(temp_file_path, 'r', encoding='utf-8') as protocol_file:
                    runlog, bundle = simulate(protocol_file)
                
                # Format the runlog for analysis
                formatted_runlog = format_runlog(runlog)
                
                # Analyze the runlog for errors and warnings
                errors, warnings = self._analyze_runlog(runlog)
                
                # Generate suggestions based on errors
                suggestions = self._generate_suggestions(errors, warnings)
                
                simulation_time = (datetime.now() - start_time).total_seconds()
                
                # Log metadata to Langfuse
                if LANGFUSE_AVAILABLE:
                    try:
                        from langfuse.decorators import langfuse_context
                        langfuse_context.update_current_observation(
                            metadata={
                                "code_length": len(code),
                                "simulation_time_seconds": simulation_time,
                                "error_count": len(errors),
                                "warning_count": len(warnings),
                                "success": len(errors) == 0
                            }
                        )
                    except Exception as e:
                        self.logger.debug(f"Failed to update Langfuse metadata: {e}")
                
                self.logger.info(f"Opentrons validation completed in {simulation_time:.2f}s - {len(errors)} errors, {len(warnings)} warnings")
                
                return ValidationResult(
                    success=len(errors) == 0,
                    errors=errors,
                    warnings=warnings,
                    runlog=formatted_runlog,
                    suggestions=suggestions,
                    simulation_time=simulation_time
                )
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.logger.error(f"Opentrons validation failed: {e}")
            
            # Extract error information for improvement suggestions
            error_msg = str(e)
            errors = [error_msg]
            suggestions = self._generate_error_suggestions(error_msg)
            
            return ValidationResult(
                success=False,
                errors=errors,
                warnings=[],
                suggestions=suggestions,
                simulation_time=(datetime.now() - start_time).total_seconds()
            )
    
    @observe(as_type="span", name="analyze_runlog")
    def _analyze_runlog(self, runlog: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Analyze runlog for errors and warnings with tracing"""
        errors = []
        warnings = []
        
        for entry in runlog:
            # Check for error-level issues
            if entry.get('level') == 'error':
                errors.append(entry.get('message', 'Unknown error'))
            elif entry.get('level') == 'warning':
                warnings.append(entry.get('message', 'Unknown warning'))
            
            # Check for specific error patterns
            message = entry.get('message', '').lower()
            if 'error' in message or 'failed' in message or 'exception' in message:
                if entry.get('level') != 'warning':
                    errors.append(entry.get('message', 'Unknown error'))
        
        return errors, warnings
    
    @observe(as_type="span", name="generate_suggestions")
    def _generate_suggestions(self, errors: List[str], warnings: List[str]) -> List[str]:
        """Generate improvement suggestions based on errors and warnings with tracing"""
        suggestions = []
        
        for error in errors:
            error_lower = error.lower()
            
            if 'import' in error_lower or 'module' in error_lower:
                suggestions.append("Check import statements and ensure all required modules are imported")
            
            if 'pipette' in error_lower:
                suggestions.append("Verify pipette configuration and tip rack setup")
            
            if 'labware' in error_lower:
                suggestions.append("Check labware definitions and deck positions")
            
            if 'volume' in error_lower or 'capacity' in error_lower:
                suggestions.append("Verify volume calculations and pipette capacity limits")
            
            if 'deck' in error_lower or 'position' in error_lower:
                suggestions.append("Check deck layout and labware positioning")
            
            if 'temperature' in error_lower:
                suggestions.append("Verify temperature module configuration and parameters")
        
        # Add general suggestions if no specific errors found
        if not suggestions and (errors or warnings):
            suggestions.append("Review protocol structure and ensure all steps are properly defined")
            suggestions.append("Check for syntax errors and proper Opentrons API usage")
        
        return suggestions
    
    def _generate_error_suggestions(self, error_msg: str) -> List[str]:
        """Generate suggestions based on specific error messages"""
        suggestions = []
        error_lower = error_msg.lower()
        
        if 'syntax' in error_lower:
            suggestions.append("Fix Python syntax errors in the protocol code")
        
        if 'indentation' in error_lower:
            suggestions.append("Check Python indentation and code structure")
        
        if 'name' in error_lower and 'not defined' in error_lower:
            suggestions.append("Define all required variables and functions before use")
        
        if 'import' in error_lower:
            suggestions.append("Add missing import statements for required modules")
        
        if 'protocol' in error_lower:
            suggestions.append("Ensure protocol function is properly defined with correct signature")
        
        return suggestions or ["Review the protocol code for common issues and try again"]


class OpentronsCodeGenerator:
    """Generates Opentrons code with validation and retry mechanism"""
    
    def __init__(self, validator: OpentronsValidator = None, mcp_client=None, llm_client=None):
        self.validator = validator or OpentronsValidator()
        self.mcp_client = mcp_client
        self.llm_client = llm_client
        self.logger = logging.getLogger("catalyze.opentrons_generator")
    
    async def generate_with_validation(
        self, 
        instructions: str, 
        context: Dict[str, Any] = None,
        platform: str = "ot2",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate Opentrons code with validation and retry mechanism
        
        Args:
            instructions: Protocol instructions
            context: Additional context for generation
            platform: 'ot2' or 'flex' - target Opentrons platform
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing generation result and metadata
        """
        self.logger.info(f"Starting Opentrons code generation for {platform.upper()} with {max_retries} retries")
        
        # Store the original instruction
        original_instruction = instructions
        
        for attempt in range(max_retries + 1):
            try:
                # Generate code (this would be done by the MCP server)
                # For now, we'll simulate this step
                code = await self._generate_code(instructions, context, attempt, platform)
                
                # Validate the generated code with platform info
                validation_result = await self.validator.validate_code(code, platform=platform)
                
                if validation_result.success:
                    self.logger.info(f"Opentrons code generated successfully on attempt {attempt + 1}")
                    return {
                        "success": True,
                        "code": code,
                        "status": "success",
                        "attempts": attempt + 1,
                        "validation_result": validation_result,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    self.logger.warning(f"Validation failed on attempt {attempt + 1}: {validation_result.errors}")
                
                if attempt < max_retries:
                    # Prepare improved instructions for next attempt
                    improved_instructions = self._improve_instructions(
                        original_instruction, 
                        validation_result.errors, 
                        validation_result.suggestions
                    )
                    # Store the improved instructions for the next iteration
                    instructions = improved_instructions
                    self.logger.info(f"Retrying with improved instructions (attempt {attempt + 2})")
                else:
                    # Max retries exceeded
                    return {
                        "success": False,
                        "code": code,
                        "status": "failed",
                        "attempts": attempt + 1,
                        "validation_result": validation_result,
                        "error": "Max retries exceeded",
                        "timestamp": datetime.now().isoformat()
                    }
                        
            except Exception as e:
                self.logger.error(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt >= max_retries:
                    return {
                        "success": False,
                        "status": "failed",
                        "attempts": attempt + 1,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
    
    async def _generate_code(self, instructions: str, context: Dict[str, Any], attempt: int, platform: str = "ot2") -> str:
        """Generate Opentrons code using MCP server documentation and LLM"""
        
        # Extract core instruction (remove any error context from retries)
        core_instruction = instructions.split('\n')[0] if '\n' in instructions else instructions
        
        # Get Opentrons documentation from MCP server
        opentrons_docs = await self._get_opentrons_documentation(core_instruction)
        
        # Create a detailed prompt for code generation
        prompt = f"""
Generate a complete Opentrons protocol based on these instructions: {core_instruction}

Target Platform: {platform.upper()}

Use this Opentrons documentation as reference:
{opentrons_docs}

Requirements:
1. Create a complete, functional Opentrons protocol
2. Include proper metadata with protocolName, author, description, and apiLevel '2.13'
3. Use appropriate labware and pipettes based on the protocol needs
4. Include proper error handling and comments
5. Make the code production-ready and ready to simulate
6. Follow Opentrons API best practices
7. Only include Python code, no explanations
8. Use correct deck slot naming for {platform.upper()}: {'numeric slots 1-11' if platform == 'ot2' else 'coordinate slots A1-D3'}

Generate the complete Python code for the protocol (ONLY code, starting with imports):
"""
        
        # Use LLM to generate the code if available
        if self.llm_client:
            try:
                system_message = f"You are an expert Opentrons protocol developer. Generate complete, valid Opentrons Python protocols for {platform.upper()} that follow the API specifications exactly."
                code = self.llm_client.generate_response(prompt, system_message)
                
                # Extract code from markdown if present
                if "```python" in code:
                    code = code.split("```python")[1].split("```")[0].strip()
                elif "```" in code:
                    code = code.split("```")[1].split("```")[0].strip()
                
                self.logger.info(f"Generated code using LLM (attempt {attempt + 1})")
                return code
            except Exception as e:
                self.logger.error(f"LLM generation failed: {e}")
                raise Exception(f"Code generation failed: LLM client not available or generation error: {e}")
        
        # If no LLM client, raise an error
        raise Exception("Code generation failed: LLM client not initialized")
    
    async def _get_opentrons_documentation(self, instructions: str) -> str:
        """Get relevant Opentrons documentation from MCP server"""
        if not self.mcp_client:
            self.logger.warning("🔧 OpentronsGenerator - MCP client not initialized")
            return "Opentrons documentation not available (MCP client not initialized)"
        
        try:
            self.logger.info(f"🔧 OpentronsGenerator - Getting Opentrons documentation for: {instructions[:50]}...")
            
            # Get available tools from MCP client
            tools = await self.mcp_client.get_tools()
            self.logger.info(f"🔧 OpentronsGenerator - Available tools: {[tool.name for tool in tools]}")
            
            # Find Opentrons Python API documentation tools
            search_tool = None
            api_ref_tool = None
            example_tool = None
            
            for tool in tools:
                tool_name_lower = tool.name.lower()
                if 'search_opentrons_docs' in tool_name_lower:
                    search_tool = tool
                    self.logger.info(f"🔧 OpentronsGenerator - Found search_opentrons_docs tool: {tool.name}")
                elif 'get_opentrons_api_reference' in tool_name_lower:
                    api_ref_tool = tool
                    self.logger.info(f"🔧 OpentronsGenerator - Found get_opentrons_api_reference tool: {tool.name}")
                elif 'get_opentrons_example' in tool_name_lower:
                    example_tool = tool
                    self.logger.info(f"🔧 OpentronsGenerator - Found get_opentrons_example tool: {tool.name}")
            
            if not search_tool and not api_ref_tool:
                self.logger.warning("🔧 OpentronsGenerator - No Opentrons Python API documentation tools available")
                return "No Opentrons Python API documentation tools available"
            
            relevant_docs = []
            
            # Extract key terms from instructions for searching
            instructions_lower = instructions.lower()
            search_terms = []
            
            # Extract platform-specific terms
            if "flex" in instructions_lower:
                search_terms.append("flex")
            if "ot-2" in instructions_lower or "ot2" in instructions_lower:
                search_terms.append("ot-2")
            
            # Extract operation terms
            if "labware" in instructions_lower:
                search_terms.append("labware")
            if "pipette" in instructions_lower:
                search_terms.append("pipette")
            if "transfer" in instructions_lower:
                search_terms.append("transfer")
            if "aspirate" in instructions_lower or "dispense" in instructions_lower:
                search_terms.append("aspirate dispense")
            if "module" in instructions_lower:
                search_terms.append("module")
            if "deck" in instructions_lower or "slot" in instructions_lower:
                search_terms.append("deck slot")
            
            # If no specific terms, use the instructions as search query
            if not search_terms:
                search_query = instructions
            else:
                search_query = " ".join(search_terms[:3])  # Use top 3 terms
            
            self.logger.info(f"🔧 OpentronsGenerator - Searching documentation with query: {search_query}")
            
            # Search for relevant documentation
            try:
                if search_tool:
                    self.logger.info(f"🔧 OpentronsGenerator - Calling search_opentrons_docs with query: {search_query}")
                    search_result = await search_tool.ainvoke({"query": search_query, "limit": 5})
                    if search_result:
                        relevant_docs.append(f"Search results: {str(search_result)}")
                        self.logger.info(f"🔧 OpentronsGenerator - search_opentrons_docs returned {len(str(search_result))} characters")
                
                # Also try to get API reference for specific topics
                if api_ref_tool and search_terms:
                    for term in search_terms[:2]:  # Try top 2 terms
                        try:
                            self.logger.info(f"🔧 OpentronsGenerator - Getting API reference for: {term}")
                            api_result = await api_ref_tool.ainvoke({"topic": term})
                            if api_result:
                                relevant_docs.append(f"API Reference for {term}: {str(api_result)}")
                                self.logger.info(f"🔧 OpentronsGenerator - API reference returned {len(str(api_result))} characters")
                                break  # Use first successful result
                        except Exception as e:
                            self.logger.debug(f"🔧 OpentronsGenerator - API reference search failed for {term}: {e}")
                            continue
                
                # Get examples if available
                if example_tool and ("transfer" in instructions_lower or "protocol" in instructions_lower):
                    try:
                        example_type = "transfer" if "transfer" in instructions_lower else "protocol"
                        self.logger.info(f"🔧 OpentronsGenerator - Getting examples for: {example_type}")
                        example_result = await example_tool.ainvoke({"example_type": example_type})
                        if example_result:
                            relevant_docs.append(f"Examples: {str(example_result)}")
                            self.logger.info(f"🔧 OpentronsGenerator - Examples returned {len(str(example_result))} characters")
                    except Exception as e:
                        self.logger.debug(f"🔧 OpentronsGenerator - Example search failed: {e}")
            
            except Exception as e:
                self.logger.warning(f"🔧 OpentronsGenerator - Documentation search failed: {e}")
                # Continue with empty docs rather than failing completely
                relevant_docs = []
            
            # Parse results if needed
            try:
                import json
                parsed_docs = []
                for doc in relevant_docs:
                    try:
                        # Try to parse JSON if it's a JSON string
                        if doc.startswith("Search results:") or doc.startswith("API Reference") or doc.startswith("Examples:"):
                            # Extract the JSON part
                            json_part = doc.split(":", 1)[1].strip() if ":" in doc else doc
                            try:
                                doc_data = json.loads(json_part)
                                # Format nicely
                                if isinstance(doc_data, dict) and "results" in doc_data:
                                    for result in doc_data.get("results", [])[:3]:  # Top 3 results
                                        parsed_docs.append(f"{result.get('title', 'Unknown')}: {result.get('content', '')[:500]}")
                                elif isinstance(doc_data, dict) and "examples" in doc_data:
                                    for example in doc_data.get("examples", [])[:2]:  # Top 2 examples
                                        parsed_docs.append(f"Example: {example.get('code', '')[:500]}")
                                else:
                                    parsed_docs.append(json_part[:1000])
                            except json.JSONDecodeError:
                                # Not JSON, use as-is
                                parsed_docs.append(doc[:1000])
                        else:
                            parsed_docs.append(doc[:1000])
                    except Exception as e:
                        self.logger.debug(f"🔧 OpentronsGenerator - Failed to parse doc: {e}")
                        parsed_docs.append(doc[:1000])
                
                if parsed_docs:
                    relevant_docs = parsed_docs
            except Exception as e:
                self.logger.debug(f"🔧 OpentronsGenerator - Failed to parse documentation: {e}")
                # Use original docs if parsing fails
                pass
            
            # Fallback: if no docs found, try a simple search
            if not relevant_docs and search_tool:
                try:
                    self.logger.info(f"🔧 OpentronsGenerator - Fallback: searching with full instructions")
                    fallback_result = await search_tool.ainvoke({"query": instructions[:200], "limit": 3})
                    if fallback_result:
                        relevant_docs.append(str(fallback_result)[:2000])
                except Exception as e:
                    self.logger.debug(f"🔧 OpentronsGenerator - Fallback search failed: {e}")
            
            # If still no docs, return a message
            if not relevant_docs:
                self.logger.warning("🔧 OpentronsGenerator - No relevant documentation found")
                return "Opentrons documentation search returned no results. Proceeding with general knowledge."
            
            # Combine all documentation into a single string
            combined_docs = "\n\n".join(relevant_docs)
            self.logger.info(f"🔧 OpentronsGenerator - Combined documentation length: {len(combined_docs)} characters")
            
            return combined_docs
            
        except Exception as e:
            self.logger.error(f"Failed to get Opentrons documentation: {e}")
            return "Opentrons documentation temporarily unavailable"
    
    def _improve_instructions(
        self, 
        instructions: str, 
        errors: List[str], 
        suggestions: List[str]
    ) -> str:
        """Improve instructions based on validation errors and suggestions"""
        error_context = "\n".join([f"- {error}" for error in errors])
        suggestion_context = "\n".join([f"- {suggestion}" for suggestion in suggestions])
        
        # Extract the core instruction - look for the original instruction
        if "Previous attempt had the following issues:" in instructions:
            # This is already an improved instruction, extract the core
            core_instruction = instructions.split('\n')[0]
        else:
            # This is the original instruction
            core_instruction = instructions
        
        improved_instructions = f"""
{core_instruction}

Previous attempt had the following issues:
{error_context}

Please address these issues:
{suggestion_context}

Generate a corrected Opentrons protocol that fixes these problems.
"""
        
        return improved_instructions
