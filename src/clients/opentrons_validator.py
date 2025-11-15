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
    
    @observe(as_type="span", name="opentrons_validation")
    async def validate_code(self, code: str) -> ValidationResult:
        """
        Validate Opentrons protocol code using simulation with Langfuse tracing
        
        Args:
            code: Python code containing Opentrons protocol
            
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
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate Opentrons code with validation and retry mechanism
        
        Args:
            instructions: Protocol instructions
            context: Additional context for generation
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing generation result and metadata
        """
        self.logger.info(f"Starting Opentrons code generation with {max_retries} retries")
        
        # Store the original instruction
        original_instruction = instructions
        
        for attempt in range(max_retries + 1):
            try:
                # Generate code (this would be done by the MCP server)
                # For now, we'll simulate this step
                code = await self._generate_code(instructions, context, attempt)
                
                # Validate the generated code
                validation_result = await self.validator.validate_code(code)
                
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
    
    async def _generate_code(self, instructions: str, context: Dict[str, Any], attempt: int) -> str:
        """Generate Opentrons code using MCP server documentation and LLM"""
        
        # Extract core instruction (remove any error context from retries)
        core_instruction = instructions.split('\n')[0] if '\n' in instructions else instructions
        
        # Get Opentrons documentation from MCP server
        opentrons_docs = await self._get_opentrons_documentation(core_instruction)
        
        # Create a detailed prompt for code generation
        prompt = f"""
Generate a complete Opentrons protocol based on these instructions: {core_instruction}

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

Generate the complete Python code for the protocol (ONLY code, starting with imports):
"""
        
        # Use LLM to generate the code if available
        if self.llm_client:
            try:
                system_message = "You are an expert Opentrons protocol developer. Generate complete, valid Opentrons Python protocols that follow the API specifications exactly."
                code = self.llm_client.generate_response(prompt, system_message)
                
                # Extract code from markdown if present
                if "```python" in code:
                    code = code.split("```python")[1].split("```")[0].strip()
                elif "```" in code:
                    code = code.split("```")[1].split("```")[0].strip()
                
                self.logger.info(f"Generated code using LLM (attempt {attempt + 1})")
                return code
            except Exception as e:
                self.logger.warning(f"LLM generation failed: {e}, falling back to templates")
        
        # Fallback to template-based generation if LLM not available
        return self._create_protocol_from_instructions(core_instruction, opentrons_docs, attempt)
    
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
            
            # Find Opentrons-related tools
            opentrons_tools = [tool for tool in tools if 'opentrons' in tool.name.lower() or 'fetch_general' in tool.name.lower() or 'list_documents' in tool.name.lower() or 'search_document' in tool.name.lower()]
            self.logger.info(f"🔧 OpentronsGenerator - Found {len(opentrons_tools)} Opentrons tools: {[tool.name for tool in opentrons_tools]}")
            
            if not opentrons_tools:
                self.logger.warning("🔧 OpentronsGenerator - No Opentrons tools available")
                return "No Opentrons tools available"
            
            # Try to get general information
            general_info = ""
            for tool in opentrons_tools:
                if 'fetch_general' in tool.name.lower():
                    try:
                        self.logger.info(f"🔧 OpentronsGenerator - Calling {tool.name}...")
                        result = await tool.ainvoke({})
                        if result:
                            general_info = str(result)
                            self.logger.info(f"🔧 OpentronsGenerator - {tool.name} returned {len(general_info)} characters")
                            break
                    except Exception as e:
                        self.logger.warning(f"🔧 OpentronsGenerator - Failed to call {tool.name}: {e}")
                        continue
            
            # Search for relevant documentation based on instructions
            docs_to_search = []
            instructions_lower = instructions.lower()
            if "flex" in instructions_lower:
                docs_to_search.append("flex-manual")
            if "ot-2" in instructions_lower or "ot2" in instructions_lower:
                docs_to_search.append("pd-manual")
            if "protocol" in instructions_lower or "code" in instructions_lower or "opentrons" in instructions_lower:
                docs_to_search.append("pd-manual")
            
            # If no specific category, search all
            if not docs_to_search:
                docs_to_search = ["pd-manual", "flex-manual"]
            
            self.logger.info(f"🔧 OpentronsGenerator - Searching documentation categories: {docs_to_search}")
            
            relevant_docs = []
            
            # Try to find list_documents and search_document tools
            list_tool = None
            search_tool = None
            
            for tool in tools:
                if 'list_documents' in tool.name.lower():
                    list_tool = tool
                    self.logger.info(f"🔧 OpentronsGenerator - Found list_documents tool: {tool.name}")
                elif 'search_document' in tool.name.lower():
                    search_tool = tool
                    self.logger.info(f"🔧 OpentronsGenerator - Found search_document tool: {tool.name}")
            
            self.logger.info(f"🔧 OpentronsGenerator - list_tool: {list_tool is not None}, search_tool: {search_tool is not None}")
            
            for category in docs_to_search:
                self.logger.info(f"🔧 OpentronsGenerator - Processing category: {category}")
                try:
                    # List documents in category
                    if list_tool:
                        self.logger.info(f"🔧 OpentronsGenerator - Calling list_documents for category: {category}")
                        doc_list = await list_tool.ainvoke({"category": category})
                        if doc_list:
                            relevant_docs.append(f"Category {category}: {str(doc_list)}")
                            self.logger.info(f"🔧 OpentronsGenerator - list_documents returned {len(str(doc_list))} characters")
                    
                    # Search for specific documents
                    if search_tool and doc_list:
                        self.logger.info(f"🔧 OpentronsGenerator - Searching specific documents in category: {category}")
                        try:
                            # Parse the JSON response to get file names
                            import json
                            doc_data = json.loads(str(doc_list))
                            files = doc_data.get("categories", [{}])[0].get("files", [])
                            self.logger.info(f"🔧 OpentronsGenerator - Found {len(files)} files in category {category}")
                            
                            # Search for relevant files based on instructions
                            relevant_files = []
                            for file in files:
                                if any(keyword in file.lower() for keyword in ["protocol", "api", "python", "script", "code"]):
                                    relevant_files.append(file)
                            
                            self.logger.info(f"🔧 OpentronsGenerator - Found {len(relevant_files)} relevant files: {relevant_files[:3]}")
                            
                            # Search specific relevant files
                            for filename in relevant_files[:3]:  # Limit to 3 most relevant files
                                try:
                                    self.logger.info(f"🔧 OpentronsGenerator - Searching document: {filename}")
                                    search_result = await search_tool.ainvoke({
                                        "filename": filename,
                                        "category": category
                                    })
                                    if search_result:
                                        relevant_docs.append(f"Document {filename}: {str(search_result)[:500]}...")
                                        self.logger.info(f"🔧 OpentronsGenerator - {filename} returned {len(str(search_result))} characters")
                                except Exception as e:
                                    self.logger.warning(f"🔧 OpentronsGenerator - Failed to search document {filename}: {e}")
                                    continue
                        except Exception as e:
                            self.logger.warning(f"🔧 OpentronsGenerator - Failed to parse document list for category {category}: {e}")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get documentation for category {category}: {e}")
                    continue
            
            # Combine all documentation
            all_docs = []
            if general_info:
                all_docs.append(f"General Opentrons Info: {general_info}")
            all_docs.extend(relevant_docs)
            
            if all_docs:
                return "\n\n".join(all_docs)
            else:
                return "No specific Opentrons documentation found for this query"
            
        except Exception as e:
            self.logger.error(f"Failed to get Opentrons documentation: {e}")
            return "Opentrons documentation temporarily unavailable"
    
    def _create_protocol_from_instructions(self, instructions: str, docs: str, attempt: int) -> str:
        """Create a protocol based on instructions and documentation"""
        
        # Extract core instruction for analysis
        if "Previous attempt had the following issues:" in instructions:
            # This is an improved instruction, extract the core
            core_instruction = instructions.split('\n')[0]
        else:
            # This is the original instruction
            core_instruction = instructions
        
        instructions_lower = core_instruction.lower()
        
        self.logger.info(f"🔧 OpentronsGenerator - Core instruction: {core_instruction[:100]}...")
        self.logger.info(f"🔧 OpentronsGenerator - Instructions lower: {instructions_lower[:100]}...")
        
        # All protocols go through the same generation method
        self.logger.info(f"🔧 OpentronsGenerator - Using Opentrons protocol generation")
        return self._create_opentrons_protocol(core_instruction, attempt)
    
    def _create_opentrons_protocol(self, instructions: str, attempt: int) -> str:
        """Create an Opentrons protocol based on instructions"""
        return f"""
from opentrons import protocol_api

metadata = {{
    'protocolName': 'Custom Protocol',
    'author': 'Catalyze AI',
    'description': 'Auto-generated Opentrons protocol',
    'apiLevel': '2.13'
}}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single', 'right', tip_racks=[tip_rack])
    
    # Add your specific protocol steps here
    pipette.pick_up_tip()
    # Example: Transfer 100µL from reservoir to plate
    pipette.aspirate(100, reservoir['A1'])
    pipette.dispense(100, plate['A1'])
    pipette.drop_tip()
    
    protocol.comment('Protocol completed successfully')
"""
    
    def _create_serial_dilution_protocol(self, instructions: str, attempt: int) -> str:
        """Create a serial dilution protocol based on detailed instructions"""
        return f"""
from opentrons import protocol_api

metadata = {{
    'protocolName': 'Serial Dilution Assay',
    'author': 'Test User',
    'description': 'Automates a 2-fold serial dilution across the first row of a 96-well plate using buffer and reagent.',
    'apiLevel': '2.13'
}}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '2')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack])
    
    # Add 100µL buffer from reservoir A1 into wells A1–A12
    pipette.pick_up_tip()
    for well in plate.rows()[0][:12]:  # A1-A12
        pipette.aspirate(100, reservoir['A1'])
        pipette.dispense(100, well)
        pipette.blow_out()
    pipette.drop_tip()
    
    # Add 100µL reagent from reservoir A2 into well A1
    pipette.pick_up_tip()
    pipette.aspirate(100, reservoir['A2'])
    pipette.dispense(100, plate['A1'])
    pipette.mix(3, 50, plate['A1'])  # Mix 3 times with 50µL
    pipette.drop_tip()
    
    # Perform 2-fold serial dilution across wells A1–A12
    for i in range(11):  # A1 to A11 (A12 is the last dilution)
        pipette.pick_up_tip()
        # Transfer 100µL from current well to next well
        pipette.aspirate(100, plate.rows()[0][i])
        pipette.dispense(100, plate.rows()[0][i+1])
        # Mix 3 times with 50µL after each dilution
        pipette.mix(3, 50, plate.rows()[0][i+1])
        pipette.drop_tip()
    
    protocol.comment('Serial dilution protocol completed successfully')
"""
    
    def _create_elisa_protocol(self, instructions: str, attempt: int) -> str:
        """Create an ELISA protocol based on detailed instructions"""
        return f"""
from opentrons import protocol_api

metadata = {{
    'protocolName': 'ELISA Plate Preparation',
    'author': 'Catalyze AI',
    'description': 'Automates ELISA plate preparation with buffer and sample addition',
    'apiLevel': '2.13'
}}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', '2')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack])
    
    # Add 100µL buffer to all wells
    pipette.pick_up_tip()
    for well in plate.wells():
        pipette.aspirate(100, reservoir['A1'])
        pipette.dispense(100, well)
        pipette.blow_out()
    pipette.drop_tip()
    
    # Add 50µL sample to wells A1-A12
    pipette.pick_up_tip()
    for i in range(12):  # A1-A12
        well_name = f'A{{i+1}}'
        pipette.aspirate(50, reservoir['A2'])
        pipette.dispense(50, plate[well_name])
        pipette.blow_out()
    pipette.drop_tip()
    
    protocol.comment('ELISA plate preparation completed successfully')
"""
    
    def _create_transfer_protocol(self, instructions: str, attempt: int) -> str:
        """Create a liquid transfer protocol"""
        return f"""
from opentrons import protocol_api

metadata = {{
    'protocolName': 'Liquid Transfer Protocol',
    'author': 'Catalyze AI',
    'description': 'Auto-generated liquid transfer protocol',
    'apiLevel': '2.13'
}}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    source_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    dest_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tip_rack])
    
    # Transfer liquid from A1 to B1
    pipette.pick_up_tip()
    pipette.aspirate(100, source_plate['A1'])
    pipette.dispense(100, dest_plate['B1'])
    pipette.drop_tip()
    
    # Additional transfers based on instructions
    # Add more specific logic based on the instructions
"""
    
    def _create_pcr_protocol(self, instructions: str, attempt: int) -> str:
        """Create a PCR protocol"""
        return f"""
from opentrons import protocol_api

metadata = {{
    'protocolName': 'PCR Setup Protocol',
    'author': 'Catalyze AI',
    'description': 'Auto-generated PCR setup protocol',
    'apiLevel': '2.13'
}}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    pcr_plate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', '2')
    reagent_plate = protocol.load_labware('nest_12_reservoir_15ml', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tip_rack])
    
    # PCR setup for 96-well plate
    for row in range(8):  # 8 rows
        for col in range(12):  # 12 columns
            well_name = chr(65 + row) + str(col + 1)  # A1, A2, ..., H12
            
            # Pick up a new tip for each well
            pipette.pick_up_tip()
            
            # Add master mix
            pipette.transfer(20, reagent_plate['A1'], pcr_plate[well_name])
            # Add template DNA
            pipette.transfer(5, reagent_plate['A2'], pcr_plate[well_name])
            # Add primers
            pipette.transfer(2, reagent_plate['A3'], pcr_plate[well_name])
            
            # Mix the reaction
            pipette.mix(3, 30, pcr_plate[well_name])
            
            # Drop the tip after each well
            pipette.drop_tip()
"""
    
    def _create_dilution_protocol(self, instructions: str, attempt: int) -> str:
        """Create a dilution protocol"""
        return f"""
from opentrons import protocol_api

metadata = {{
    'protocolName': 'Dilution Protocol',
    'author': 'Catalyze AI',
    'description': 'Auto-generated dilution protocol',
    'apiLevel': '2.13'
}}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    source_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    dest_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '3')
    diluent_plate = protocol.load_labware('nest_12_reservoir_15ml', '4')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tip_rack])
    
    # Perform dilutions
    for i in range(8):  # 8 dilutions
        pipette.pick_up_tip()
        # Transfer sample
        pipette.transfer(10, source_plate[f'A{{i+1}}'], dest_plate[f'A{{i+1}}'])
        # Add diluent
        pipette.transfer(90, diluent_plate['A1'], dest_plate[f'A{{i+1}}'])
        # Mix
        pipette.mix(3, 50, dest_plate[f'A{{i+1}}'])
        pipette.drop_tip()
"""
    
    def _create_general_protocol(self, instructions: str, attempt: int) -> str:
        """Create a general protocol"""
        return f"""
from opentrons import protocol_api

metadata = {{
    'protocolName': 'Custom Protocol',
    'author': 'Catalyze AI',
    'description': 'Auto-generated protocol based on instructions',
    'apiLevel': '2.13'
}}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tip_rack])
    
    # Protocol implementation based on: {instructions}
    # Add specific steps based on the instructions
    pipette.pick_up_tip()
    # Add your protocol steps here
    pipette.drop_tip()
"""
    
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
