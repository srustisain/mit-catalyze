"""
Base Agent Class

Provides common functionality for all specialized agents including:
- Tool management and MCP integration
- Response formatting and error handling
- Logging and debugging capabilities
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.clients.llm_client import LLMClient
from src.config.config import OPENAI_MODEL, MCP_SERVERS, LANGFUSE_ENABLED, OPENAI_API_KEY
from src.evaluation.async_scorer import AsyncScorer
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

# Try to import Langfuse, but make it optional
try:
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    logging.warning("langfuse not available. Tracing will be disabled.")
    LangfuseCallbackHandler = None
    LANGFUSE_AVAILABLE = False
from src.prompts import load_prompt
from src.config.logging_config import get_logger

# Try to import MCP client, but make it optional
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: langchain_mcp_adapters not available. MCP functionality will be disabled.")
    MultiServerMCPClient = None
    MCP_AVAILABLE = False


class BaseAgent(ABC):
    """Base class for all Catalyze agents"""
    
    def __init__(self, name: str, description: str, tools: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.llm_client = LLMClient(provider="openai")
        self.logger = get_logger(f"catalyze.{name.lower()}")
        
        # MCP client for tool access
        self.mcp_client = None
        self.agent = None
        
        # LangGraph memory checkpointer for conversation state
        self.checkpointer = MemorySaver()
        self.logger.debug(f"Initialized LangGraph MemorySaver for {self.name}")
        
        # Initialize Langfuse callback handler
        self.langfuse_handler = None
        if LANGFUSE_AVAILABLE and LANGFUSE_ENABLED:
            try:
                self.langfuse_handler = LangfuseCallbackHandler()
                self.logger.debug(f"Langfuse tracing enabled for {self.name}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Langfuse for {self.name}: {e}")
                self.langfuse_handler = None
        
    async def initialize(self):
        """Initialize the agent with MCP tools"""
        try:
            if not MCP_AVAILABLE:
                self.logger.warning(f"MCP not available, initializing {self.name} without tools")
                self.mcp_client = None
                self.agent = None
                return
                
            if not MCP_SERVERS:
                self.logger.warning(f"No MCP servers configured, initializing {self.name} without tools")
                self.mcp_client = None
                self.agent = None
                return
            
            # Determine which MCP servers this agent should use
            server_config = self._get_agent_server_config()
            if not server_config:
                self.logger.warning(f"No appropriate MCP servers for {self.name}")
                self.mcp_client = None
                self.agent = None
                return
            
            # Create MCP client with only the relevant servers
            self.mcp_client = MultiServerMCPClient(server_config)
            available_tools = await self.mcp_client.get_tools()
            
            self.logger.debug(f"{self.name} - MCP client loaded {len(available_tools)} total tools from {list(server_config.keys())}")
            self.logger.debug(f"{self.name} - Available tool names: {[tool.name for tool in available_tools]}")
            
            # Filter out non-functional tools (like search_drugs which returns "not yet implemented")
            non_functional_tools = ['search_drugs']  # Add more as needed
            available_tools = [tool for tool in available_tools if tool.name not in non_functional_tools]
            if non_functional_tools:
                self.logger.info(f"🚫 {self.name} filtered out non-functional tools: {non_functional_tools}")
            
            # Filter tools based on agent specialization (if specific tools are requested)
            if self.tools:
                available_tool_names = [tool.name for tool in available_tools]
                requested_tools = self.tools
                missing_tools = [t for t in requested_tools if t not in available_tool_names]
                
                if missing_tools:
                    self.logger.warning(f"⚠️  {self.name} requested tools not found: {missing_tools}")
                    self.logger.warning(f"   Available tools from MCP: {available_tool_names}")
                
                available_tools = [tool for tool in available_tools if tool.name in self.tools]
                self.logger.info(f"✅ {self.name} filtered to {len(available_tools)} tools: {[t.name for t in available_tools]}")
            else:
                self.logger.info(f"✅ {self.name} using all {len(available_tools)} available tools: {[t.name for t in available_tools]}")
            
            self.logger.debug(f"Initialized {self.name} with {len(available_tools)} tools from {list(server_config.keys())}")
            
            # Create LangGraph agent with MCP tools if we have tools
            if available_tools and OPENAI_API_KEY:
                try:
                    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
                    # Create ReAct agent with memory checkpointer for conversation state
                    self.agent = create_react_agent(llm, available_tools, checkpointer=self.checkpointer)
                    self.logger.debug(f"Created LangGraph agent for {self.name} with {len(available_tools)} tools and memory")
                except Exception as e:
                    self.logger.warning(f"Failed to create LangGraph agent: {e}")
                    self.agent = None
            else:
                self.agent = None
                if not available_tools:
                    self.logger.warning(f"No tools available for {self.name}")
                if not OPENAI_API_KEY:
                    self.logger.warning(f"No OpenAI API key configured")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize {self.name} with MCP tools: {e}")
            self.logger.info(f"Initializing {self.name} without tools as fallback")
            self.mcp_client = None
            self.agent = None
    
    def _get_agent_server_config(self) -> Dict[str, Any]:
        """Get the appropriate MCP server configuration for this agent"""
        # Determine server based on agent name (simpler and more reliable)
        agent_name_lower = self.name.lower()
        
        # ChEMBL agents: ResearchAgent, ProtocolAgent, SafetyAgent
        if any(name in agent_name_lower for name in ["research", "protocol", "safety"]):
            if "chembl" in MCP_SERVERS:
                return {"chembl": MCP_SERVERS["chembl"]}
        
        # Opentrons agent: AutomateAgent
        if "automate" in agent_name_lower:
            if "opentrons_python_api" in MCP_SERVERS:
                return {"opentrons_python_api": MCP_SERVERS["opentrons_python_api"]}
        
        # Fallback: Check tools if specified (for backward compatibility)
        if self.tools:
            chembl_tools = ["search_compounds", "get_compound_info", "search_targets", "get_target_info", 
                            "search_activities", "get_assay_info", "search_drugs", "get_drug_info"]
            opentrons_tools = ["search_opentrons_docs", "get_opentrons_api_reference", "get_opentrons_example", "update_opentrons_docs"]
            
            if any(tool in self.tools for tool in chembl_tools):
                if "chembl" in MCP_SERVERS:
                    return {"chembl": MCP_SERVERS["chembl"]}
            
            if any(tool in self.tools for tool in opentrons_tools):
                if "opentrons_python_api" in MCP_SERVERS:
                    return {"opentrons_python_api": MCP_SERVERS["opentrons_python_api"]}
        
        # Default to no servers if no match
        return {}
    
    
    @abstractmethod
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query using the agent's specialized capabilities
        
        Args:
            query: The user's query
            context: Additional context (conversation history, mode, etc.)
            
        Returns:
            Dictionary containing the agent's response and metadata
        """
        pass
    
    def get_system_prompt(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get the system prompt for this agent with optional context-based modifications"""
        from src.utils import prompt_manager
        
        # Map agent class names to Langfuse prompt names
        prompt_mapping = {
            'ResearchAgent': 'research-agent-prompt',
            'ProtocolAgent': 'protocol-agent-prompt', 
            'AutomateAgent': 'automate-agent-prompt',
            'SafetyAgent': 'safety-agent-prompt'
        }
        
        class_name = self.__class__.__name__
        langfuse_prompt_name = prompt_mapping.get(class_name)
        
        if langfuse_prompt_name:
            # Try to get prompt from Langfuse with A/B testing support
            ab_test_enabled = context and context.get("ab_test", False)
            
            if ab_test_enabled:
                # Use A/B testing between production-a and production-b
                prompt_data = prompt_manager.ab_test_prompts(
                    langfuse_prompt_name,
                    labels=["production-a", "production-b"],
                    weights=[0.5, 0.5]  # 50/50 split
                )
            else:
                # Use standard production prompt
                prompt_data = prompt_manager.get_prompt_with_config(
                    langfuse_prompt_name, 
                    label="production"
                )
            
            if prompt_data.get("prompt"):
                prompt_template = prompt_data["prompt"]
                # Check if Langfuse prompt has tool instructions - if not, use local file
                if "CRITICAL: Use Available Tools" not in prompt_template and "MUST use the available tools" not in prompt_template and class_name == "ProtocolAgent":
                    self.logger.info(f"Langfuse prompt missing tool instructions, using local file for {class_name}")
                    prompt_template = self._get_fallback_prompt(class_name)
                    prompt_data = {"prompt": prompt_template, "config": {}, "version": None, "name": langfuse_prompt_name}
                else:
                    # Log prompt source clearly
                    version = prompt_data.get('version', 'unknown')
                    source = f"Langfuse prompt: {langfuse_prompt_name} v{version} (production)"
                    self.logger.info(f"📝 {self.name} - {source}")
            else:
                # Fallback to local file
                prompt_template = self._get_fallback_prompt(class_name)
                prompt_data = {"prompt": prompt_template, "config": {}, "version": None, "name": langfuse_prompt_name}
                self.logger.info(f"📝 {self.name} - Using local file: src/prompts/{class_name.lower().replace('agent', '_agent')}.txt")
        else:
            # Fallback for unmapped agents
            prompt_template = self._get_fallback_prompt(class_name)
            prompt_data = {"prompt": prompt_template, "config": {}, "version": None, "name": class_name}
            self.logger.info(f"📝 {self.name} - Using fallback prompt")
        
        # Return prompt data with source tracking
        prompt_data["prompt"] = prompt_template
        prompt_data["source"] = "langfuse" if prompt_data.get("langfuse_prompt") else "local_file" if langfuse_prompt_name else "fallback"
        return prompt_data
    
    def _get_fallback_prompt(self, class_name: str) -> str:
        """Get fallback prompt from local file or default"""
        try:
            # Try to load from prompt file first
            file_name = class_name.lower().replace('agent', '_agent')
            from src.prompts import load_prompt
            return load_prompt(file_name)
        except (FileNotFoundError, ImportError):
            # Fallback to default prompt
            return f"""You are {self.name}, a specialized AI agent for chemistry tasks.

{self.description}

You have access to specialized tools and databases to help with your tasks.
Always provide accurate, detailed responses and cite your sources when possible.
Please format your responses in well-structured markdown for better readability.
"""
    
    async def _run_agent_safely(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Safely run the LangGraph agent with error handling"""
        try:
            if not self.agent:
                await self.initialize()
            
            # If agent is still None after initialization, return fallback response
            if not self.agent:
                self.logger.warning(f"Agent {self.name} not available, using fallback response")
                return {
                    "success": False,
                    "error": "Agent not available (MCP tools failed to initialize)",
                    "agent": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # LangGraph ReAct agents expect messages in LangChain message format
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            
            # Get system prompt with Langfuse integration
            prompt_data = self.get_system_prompt(context)
            system_prompt = prompt_data["prompt"]
            
            if context and context.get("memory_context"):
                memory_context = context["memory_context"]
                system_prompt += f"\n\n### Previous Conversation Context\n{memory_context}"
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            # Prepare config with thread_id for LangGraph memory and Langfuse callbacks
            config = {
                "configurable": {},
                "recursion_limit": 10  # Limit to 10 iterations max to prevent redundant tool calls
            }
            
            # Set thread_id for LangGraph's checkpointer (enables conversation memory)
            if context and context.get("thread_id"):
                config["configurable"]["thread_id"] = context["thread_id"]
                self.logger.debug(f"Using thread_id: {context['thread_id'][:8]}... for conversation memory")
            
            # Add Langfuse callbacks if available
            if self.langfuse_handler:
                config["callbacks"] = [self.langfuse_handler]
                config["run_name"] = f"{self.name}_query"
                config["tags"] = [self.name, "langgraph", "mcp"]
                
                # Link Langfuse prompt to the generation for tracking
                if prompt_data.get("langfuse_prompt"):
                    config["langfuse_prompt"] = prompt_data["langfuse_prompt"]
                    self.logger.debug(f"Linked Langfuse prompt {prompt_data['name']} v{prompt_data.get('version', 'unknown')} to generation")
                
                # Set session_id for Langfuse tracking
                if context and context.get("session_id"):
                    self.langfuse_handler.session_id = context["session_id"]
            
            # Show spinner animation (for terminal output)
            import sys
            import threading
            import time
            
            spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            spinner_running = True
            spinner_index = 0
            
            def update_spinner():
                """Update spinner in place"""
                nonlocal spinner_index
                while spinner_running:
                    char = spinner_chars[spinner_index % len(spinner_chars)]
                    sys.stdout.write(f'\r🤖 {self.name} processing... {char}')
                    sys.stdout.flush()
                    spinner_index += 1
                    time.sleep(0.1)
            
            # Start spinner thread
            spinner_thread = threading.Thread(target=update_spinner, daemon=True)
            spinner_thread.start()
            
            try:
                # Invoke LangGraph agent
                result = await self.agent.ainvoke({"messages": messages}, config=config)
            finally:
                # Stop spinner and clear line
                spinner_running = False
                time.sleep(0.15)  # Let spinner finish current cycle
                sys.stdout.write('\r' + ' ' * 60 + '\r')  # Clear spinner line
                sys.stdout.flush()
            
            # Extract final response from result
            final_messages = result.get("messages", []) if result else []
            tool_calls_made = []
            
            # Extract tool calls from messages
            for message in final_messages:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        # Handle both dict and object formats
                        if isinstance(tool_call, dict):
                            tool_name = tool_call.get('name', 'unknown')
                            tool_args = tool_call.get('args', {})
                            tool_id = tool_call.get('id', 'unknown')
                        else:
                            tool_name = getattr(tool_call, 'name', 'unknown')
                            tool_args = getattr(tool_call, 'args', {})
                            tool_id = getattr(tool_call, 'id', 'unknown')
                        
                        tool_calls_made.append({
                            'tool_name': tool_name,
                            'args': tool_args,
                            'id': tool_id
                        })
            
            # Extract response text
            if final_messages:
                last_message = final_messages[-1]
                response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response_text = "No response generated"
            
            # Log completion summary
            self.logger.info(f"✓ {self.name} completed with {len(final_messages)} messages")
            
            # Log tool usage summary
            if tool_calls_made:
                self.logger.info(f"🔧 {self.name} made {len(tool_calls_made)} tool calls: {[tc['tool_name'] for tc in tool_calls_made]}")
            else:
                self.logger.warning(f"⚠️  {self.name} completed WITHOUT using any tools")
            
            # Trigger async scoring (non-blocking, fire-and-forget)
            if LANGFUSE_ENABLED:
                try:
                    AsyncScorer.trigger_async_scoring(
                        query=query,
                        output=response_text,
                        context=context,
                        agent_name=self.name
                    )
                except Exception as e:
                    # Silently fail - scoring should never interrupt main flow
                    self.logger.debug(f"Async scoring trigger failed: {e}")
            
            # Add prompt metadata to response
            response_data = {
                "success": True,
                "response": response_text,
                "messages": final_messages,
                "agent": self.name,
                "tool_calls": tool_calls_made,
                "timestamp": datetime.now().isoformat(),
                "prompt_metadata": {
                    "source": prompt_data.get("source", "unknown"),
                    "name": prompt_data.get("name", "unknown"),
                    "version": prompt_data.get("version"),
                    "has_langfuse_prompt": bool(prompt_data.get("langfuse_prompt"))
                }
            }
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def format_response(self, result: Dict[str, Any]) -> str:
        """Format the agent's response for display"""
        if not result.get("success"):
            return f"Sorry, I encountered an error: {result.get('error', 'Unknown error')}"
        
        messages = result.get("response", [])
        if not messages:
            return "I processed your request but didn't generate a response."
        
        # Extract the final assistant message
        for message in reversed(messages):
            if hasattr(message, 'content') and message.content:
                return message.content
        
        return "I processed your request successfully."
    
    def log_interaction(self, query: str, response: str, success: bool = True):
        """Log agent interactions for debugging"""
        status = "SUCCESS" if success else "ERROR"
        self.logger.info(f"{status} - Query: {query[:50]}... - Response: {len(response)} chars")
