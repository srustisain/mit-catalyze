"""
Chat API Endpoints

Clean API endpoints for chat functionality with agent-based processing.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
import base64
import io
from openai import OpenAI

from src.pipeline import PipelineManager, ModeProcessor


class ChatEndpoints:
    """Handles chat API endpoints with agent-based processing"""
    
    def __init__(self):
        self.logger = logging.getLogger("catalyze.api")
        self.pipeline_manager = PipelineManager()
        self.mode_processor = ModeProcessor()
        self._initialized = False
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def _clean_text_formatting(self, text: str) -> str:
        """Clean text formatting while preserving markdown for better readability"""
        return text
        # if not text:
        #     return text
        
        # # # Remove markdown formatting
        # # text = text.replace('**', '')  # Remove bold markers
        # # text = text.replace('*', '')   # Remove italic markers
        # # text = text.replace('##', '')  # Remove header markers
        # # text = text.replace('#', '')   # Remove remaining header markers
        # # text = text.replace('`', '')   # Remove code markers
        # # text = text.replace('__', '')  # Remove underline markers
        # # text = text.replace('_', '')   # Remove remaining underline markers
        
        # # Improve line breaks - ensure proper spacing
        # # text = text.replace('\n\n\n', '\n\n')  # Remove triple line breaks
        # # text = text.replace('\n\n\n\n', '\n\n')  # Remove quadruple line breaks
        # # text = text.replace('\n\n\n\n\n', '\n\n')  # Remove quintuple line breaks
        
        # # Add line breaks before common section headers
        # text = text.replace('Database Safety Information:', '\n\nDatabase Safety Information:')
        # text = text.replace('Additional Database Information:', '\n\nAdditional Database Information:')
        # text = text.replace('Chemical Data for Protocol:', '\n\nChemical Data for Protocol:')
        # text = text.replace('Chemical Parameters for Automation:', '\n\nChemical Parameters for Automation:')
        # text = text.replace('PDF Document Context:', '\n\nPDF Document Context:')
        
        # # Clean up repetitive content that might appear
        # text = text.replace('ChEMBL Database: You are a Research Agent specialized in chemistry research and explanations.', '')
        # text = text.replace('Your capabilities include:', '\n\nYour capabilities include:')
        # text = text.replace('When answering questions:', '\n\nWhen answering questions:')
        # text = text.replace('Always prioritize accuracy and provide comprehensive information.', '')
        
        # # Remove verbose ChEMBL JSON data that clutters responses
        # if 'ChEMBL Database: {' in text:
        #     # Find the start and end of the JSON block
        #     start = text.find('ChEMBL Database: {')
        #     if start != -1:
        #         # Find the end of the JSON block (look for the closing brace)
        #         brace_count = 0
        #         end = start
        #         for i, char in enumerate(text[start:], start):
        #             if char == '{':
        #                 brace_count += 1
        #             elif char == '}':
        #                 brace_count -= 1
        #                 if brace_count == 0:
        #                     end = i + 1
        #                     break
                
        #         if end > start:
        #             # Replace the entire JSON block with a cleaner summary
        #             json_block = text[start:end]
        #             text = text.replace(json_block, '\n\nAdditional Database Information:\nDetailed chemical data retrieved from ChEMBL database.')
        
        # # Fix line breaks for lists and structured content
        # text = text.replace('- ', '\n- ')  # Ensure bullet points are on new lines
        # text = text.replace('1. ', '\n1. ')  # Ensure numbered lists are on new lines
        # text = text.replace('2. ', '\n2. ')  # Ensure numbered lists are on new lines
        # text = text.replace('3. ', '\n3. ')  # Ensure numbered lists are on new lines
        # text = text.replace('4. ', '\n4. ')  # Ensure numbered lists are on new lines
        # text = text.replace('5. ', '\n5. ')  # Ensure numbered lists are on new lines
        
        # # Fix line breaks for common patterns
        # text = text.replace('• ', '\n• ')  # Ensure bullet points are on new lines
        # text = text.replace('* ', '\n* ')  # Ensure asterisk lists are on new lines
        
        # # Clean up any remaining formatting artifacts
        # text = text.replace('  ', ' ')  # Remove double spaces
        # text = text.replace('\n ', '\n')  # Remove spaces at start of lines
        # text = text.replace(' \n', '\n')  # Remove spaces at end of lines
        # text = text.strip()  # Remove leading/trailing whitespace
        
        # # Remove empty lines at the beginning
        # while text.startswith('\n'):
        #     text = text[1:]
        
        # # Ensure proper spacing between list items
        # text = text.replace('\n-', '\n\n-')  # Add space before bullet points
        # text = text.replace('\n1.', '\n\n1.')  # Add space before numbered items
        # text = text.replace('\n2.', '\n\n2.')  # Add space before numbered items
        # text = text.replace('\n3.', '\n\n3.')  # Add space before numbered items
        # text = text.replace('\n4.', '\n\n4.')  # Add space before numbered items
        # text = text.replace('\n5.', '\n\n5.')  # Add space before numbered items
        # text = text.replace('\n•', '\n\n•')  # Add space before bullet points
        # text = text.replace('\n*', '\n\n*')  # Add space before asterisk points
        
        # # Clean up any triple line breaks that might have been created
        # text = text.replace('\n\n\n', '\n\n')
        
        # return text
    
    async def initialize(self):
        """Initialize the pipeline manager"""
        if not self._initialized:
            await self.pipeline_manager.initialize()
            self._initialized = True
            self.logger.info("Chat endpoints initialized")
    
    async def process_chat_message(self, message: str, mode: str = "research", 
                                 conversation_history: Optional[list] = None,
                                 pdf_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a chat message through the agent pipeline
        
        Args:
            message: The user's message
            mode: The current mode (research, protocol, automate, safety)
            conversation_history: Previous conversation messages
            pdf_context: PDF context if available
            
        Returns:
            Dictionary containing the response and metadata
        """
        
        if not self._initialized:
            await self.initialize()
        
        # Validate and normalize the mode
        validated_mode = self.mode_processor.validate_mode(mode)
        
        # Prepare context
        context = {
            "mode": validated_mode.value,
            "conversation_history": conversation_history or [],
            "timestamp": datetime.now().isoformat(),
            "pdf_context": pdf_context
        }
        
        self.logger.info(f"Processing chat message in {validated_mode.value} mode")
        
        try:
            # Check if this is a platform selection response
            if self._is_platform_selection_response(message, conversation_history):
                result = await self._handle_platform_selection(message, conversation_history, context)
            else:
                # Process through the pipeline
                result = await self.pipeline_manager.process_query(
                    query=message,
                    mode=validated_mode.value,
                    context=context
                )
            
            # Clean and format the response
            raw_response = result.get("response", "No response generated")
            cleaned_response = self._clean_text_formatting(raw_response)
            
            response_data = {
                "response": cleaned_response,
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
                "used_mcp": result.get("used_mcp", False),
                "agent_used": result.get("agent_used", validated_mode.value),
                "mode": validated_mode.value,
                "success": result.get("success", True)
            }
            
            # Add platform-specific code if present
            if "opentrons_code" in result:
                response_data["opentrons_code"] = result["opentrons_code"]
            if "lynx_code" in result:
                response_data["lynx_code"] = result["lynx_code"]
            if "platform" in result:
                response_data["platform"] = result["platform"]
            if "language" in result:
                response_data["language"] = result["language"]
            
            # Add error information if present
            if not result.get("success"):
                response_data["error"] = result.get("error", "Unknown error")
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Chat processing failed: {e}")
            return {
                "response": "Sorry, I encountered an error processing your request. Please try again.",
                "timestamp": datetime.now().isoformat(),
                "used_mcp": False,
                "agent_used": validated_mode.value,
                "mode": validated_mode.value,
                "success": False,
                "error": str(e)
            }
    
    def _is_platform_selection_response(self, message: str, conversation_history: Optional[list] = None) -> bool:
        """Check if this message is a response to a platform selection request"""
        message_lower = message.lower().strip()
        
        # First check if the message itself looks like a platform choice
        platform_choices = ["opentrons", "ot2", "ot-2", "ot 2", "lynx", "c#", "csharp", "1", "2"]
        is_platform_choice = any(choice in message_lower for choice in platform_choices)
        
        if is_platform_choice:
            # If it looks like a platform choice, check if we have conversation history
            if conversation_history:
                # Check if the last message from the system was asking for platform selection
                for msg in reversed(conversation_history[-3:]):  # Check last 3 messages
                    if msg.get("role") == "assistant" and "Platform Selection Required" in msg.get("content", ""):
                        return True
            
            # If no conversation history or no platform selection found, 
            # but message looks like a platform choice, assume it's a response
            return True
        
        return False
    
    async def _handle_platform_selection(self, message: str, conversation_history: Optional[list] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle user's platform selection response"""
        
        # Extract platform choice from message
        platform = self._extract_platform_choice(message)
        
        if not platform:
            return {
                "success": False,
                "response": "I didn't understand your platform choice. Please respond with 'OpenTrons' or 'Lynx'.",
                "agent_used": "automate",
                "timestamp": datetime.now().isoformat()
            }
        
        # Find the original query from conversation history
        original_query = self._find_original_query(conversation_history)
        
        if not original_query:
            return {
                "success": False,
                "response": "I couldn't find your original request. Please try asking again.",
                "agent_used": "automate",
                "timestamp": datetime.now().isoformat()
            }
        
        # Process the original query with the selected platform
        return await self.pipeline_manager.process_query(
            query=f"{original_query} (platform: {platform})",
            mode="automate",
            context=context
        )
    
    def _extract_platform_choice(self, message: str) -> str:
        """Extract platform choice from user message"""
        message_lower = message.lower().strip()
        
        # Check for OpenTrons choices
        opentrons_choices = ["opentrons", "ot2", "ot-2", "ot 2", "opentrons ot2", "1", "python"]
        if any(choice in message_lower for choice in opentrons_choices):
            return "opentrons"
        
        # Check for Lynx choices
        lynx_choices = ["lynx", "dynamic device", "dynamic device lynx", "c#", "csharp", "2", "c sharp"]
        if any(choice in message_lower for choice in lynx_choices):
            return "lynx"
        
        return None
    
    def _find_original_query(self, conversation_history: Optional[list] = None) -> str:
        """Find the original query that triggered platform selection"""
        if not conversation_history:
            # If no conversation history, return a generic code generation request
            return "generate code for protocol"
        
        # Look for the last user message that contains code generation keywords
        for msg in reversed(conversation_history):
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                # Check if this looks like a code generation request
                code_keywords = ["generate code", "create code", "write code", "make code", "generate script", "create script"]
                if any(keyword in content for keyword in code_keywords):
                    return msg.get("content", "")
        
        # Fallback: return the last user message
        for msg in reversed(conversation_history):
            if msg.get("role") == "user":
                return msg.get("content", "")
        
        # Final fallback
        return "generate code for protocol"
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """Get information about available agents"""
        if not self._initialized:
            await self.initialize()
        
        return await self.pipeline_manager.get_agent_capabilities()
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get pipeline status information"""
        if not self._initialized:
            await self.initialize()
        
        return self.pipeline_manager.get_status()
    
    def validate_request(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate incoming request data
        
        Args:
            data: Request data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        if not isinstance(data, dict):
            return False, "Request data must be a dictionary"
        
        if "message" not in data:
            return False, "Message is required"
        
        message = data.get("message", "").strip()
        if not message:
            return False, "Message cannot be empty"
        
        # Validate mode if provided
        if "mode" in data:
            mode = data.get("mode", "research")
            try:
                self.mode_processor.validate_mode(mode)
            except ValueError:
                return False, f"Invalid mode: {mode}. Must be one of: research, protocol, automate, safety"
        
        return True, ""
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF using available libraries
        Falls back to different methods if one fails
        """
        try:
            # Try PyMuPDF first (faster and more reliable)
            return self._extract_with_pymupdf(pdf_path)
        except ImportError:
            try:
                # Try PyPDF2 as fallback
                return self._extract_with_pypdf2(pdf_path)
            except ImportError:
                # If no PDF libraries available, try basic file reading
                return self._extract_with_basic_reading(pdf_path)
    
    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (fitz)"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip()
        except Exception as e:
            self.logger.error(f"PyMuPDF extraction failed: {e}")
            raise
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2"""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction failed: {e}")
            raise
    
    def _extract_with_basic_reading(self, pdf_path: str) -> str:
        """Basic fallback - just read the file (won't work for most PDFs)"""
        try:
            with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            self.logger.error(f"Basic reading failed: {e}")
            raise ValueError("No PDF text extraction libraries available. Please install PyMuPDF or PyPDF2.")
    
    async def process_pdf(self, pdf_path: str, filename: str) -> Dict[str, Any]:
        """
        Process PDF file with OpenAI and extract text content
        
        Args:
            pdf_path: Path to the PDF file
            filename: Original filename
            
        Returns:
            Dictionary containing processed PDF data
        """
        try:
            self.logger.info(f"Processing PDF: {filename}")
            
            # Check if file exists and is readable
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Extract text from PDF using local processing
            extracted_text = self._extract_pdf_text(pdf_path)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                raise ValueError("Could not extract meaningful text from PDF. The PDF may be image-only or corrupted.")
            
            # Check if OpenAI API key is available
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("OpenAI API key not configured")
            
            # Use OpenAI to analyze the extracted text
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a scientific document analyzer. Analyze and summarize the key content from this scientific document. Focus on:\n\n1. **Document Overview**: Title, authors, publication details\n2. **Abstract/Summary**: Main objectives and findings\n3. **Key Methods**: Experimental procedures and techniques\n4. **Results & Data**: Important findings, measurements, observations\n5. **Conclusions**: Main conclusions and implications\n6. **Chemical Information**: Compounds, reactions, molecular structures, properties\n7. **Safety Information**: Hazards, precautions, safety measures\n\nProvide a clear, structured summary that can be referenced when answering questions about this document. Be specific and include relevant numbers, formulas, and technical details. Please format your response in well-structured markdown for better readability."
                    },
                    {
                        "role": "user",
                        "content": f"Please analyze this scientific document titled '{filename}' and extract the key information:\n\n{extracted_text}"
                    }
                ],
                max_tokens=4000,
                timeout=60  # 60 second timeout
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise ValueError("OpenAI returned empty response")
            
            extracted_content = response.choices[0].message.content
            
            # Validate extracted content
            if len(extracted_content.strip()) < 50:
                raise ValueError("Extracted content is too short, PDF may be corrupted or unreadable")
            
            # Get file size for context
            file_size = os.path.getsize(pdf_path)
            
            # Create PDF context object
            pdf_context = {
                "filename": filename,
                "content": extracted_content,
                "upload_time": datetime.now().isoformat(),
                "file_size": file_size
            }
            
            self.logger.info(f"PDF processed successfully: {len(extracted_content)} characters extracted")
            
            return {
                "success": True,
                "filename": filename,
                "content": extracted_content,
                "file_size": file_size,
                "timestamp": datetime.now().isoformat()
            }
            
        except FileNotFoundError as e:
            self.logger.error(f"PDF file not found: {e}")
            return {
                "success": False,
                "error": "PDF file not found",
                "filename": filename,
                "timestamp": datetime.now().isoformat()
            }
        except ValueError as e:
            self.logger.error(f"PDF validation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"PDF processing failed: {e}")
            return {
                "success": False,
                "error": f"Failed to process PDF: {str(e)}",
                "filename": filename,
                "timestamp": datetime.now().isoformat()
            }
