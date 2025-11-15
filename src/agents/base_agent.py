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
from src.utils.mcp_response_filter import MCPResponseFilter
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
        
        # MCP response filter to reduce token usage (50K -> 2K tokens)
        self.response_filter = MCPResponseFilter()
        
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
            
            # Filter tools based on agent specialization
            if self.tools:
                available_tools = [tool for tool in available_tools if tool.name in self.tools]
                self.logger.debug(f"{self.name} - Filtered to {len(available_tools)} tools matching {self.tools}")
                self.logger.debug(f"{self.name} - Filtered tool names: {[tool.name for tool in available_tools]}")
            
            # Wrap tools with response filtering to reduce token usage
            available_tools = self._wrap_tools_with_filtering(available_tools)
            
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
        # ChEMBL tools for research, protocol, and safety agents
        chembl_tools = ["search_compounds", "get_compound_info", "search_targets", "get_target_info", 
                        "search_activities", "get_assay_info", "search_drugs", "get_drug_info"]
        
        # Opentrons tools for automate agent
        opentrons_tools = ["fetch_general", "list_documents", "search_document"]
        
        # Check if this agent uses ChEMBL tools
        if any(tool in self.tools for tool in chembl_tools):
            return {"chembl": MCP_SERVERS["chembl"]}
        
        # Check if this agent uses Opentrons tools
        if any(tool in self.tools for tool in opentrons_tools):
            return {"opentrons": MCP_SERVERS["opentrons"]}
        
        # Default to no servers if no matching tools
        return {}
    
    def _wrap_tools_with_filtering(self, tools: List[Any]) -> List[Any]:
        """Wrap MCP tools with aggressive response filtering to prevent 100K+ token responses"""
        from langchain_core.tools import StructuredTool
        
        wrapped_tools = []
        for tool in tools:
            # Create wrapper class that inherits from the tool's class
            # This ensures we maintain all LangChain tool functionality
            class FilteredTool(tool.__class__):
                def __init__(self, original_tool, response_filter, logger):
                    # Copy all attributes from original tool
                    self.__dict__.update(original_tool.__dict__)
                    self._original_tool = original_tool
                    self._response_filter = response_filter
                    self._logger = logger
                
                async def _arun(self, *args, config=None, **kwargs):
                    """Async run with filtering - config parameter required by LangChain"""
                    try:
                        # Call original tool's _arun with config
                        result = await self._original_tool._arun(*args, config=config, **kwargs)
                        
                        # Log original size (only if large)
                        original_tokens = self._response_filter.estimate_token_count(result)
                        
                        if original_tokens > 10000:
                            self._logger.warning(f"⚠️  {self.name} returned {original_tokens} tokens - applying filtering")
                        
                        # Apply filtering
                        filtered = self._response_filter.filter_response(result, self.name)
                        filtered_tokens = self._response_filter.estimate_token_count(filtered)
                        
                        # Log final result (only if significant reduction)
                        if original_tokens > 10000:
                            reduction = ((original_tokens - filtered_tokens) / original_tokens * 100) if original_tokens > 0 else 0
                            self._logger.info(f"✂️  {self.name}: {original_tokens}→{filtered_tokens} tokens ({reduction:.0f}% reduction)")
                        
                        return filtered
                    except Exception as e:
                        self._logger.error(f"Tool {self.name} failed: {e}")
                        raise
                
                def _run(self, *args, config=None, **kwargs):
                    """Sync run with filtering - config parameter required by LangChain"""
                    # For sync calls, just call original (most MCP tools are async)
                    return self._original_tool._run(*args, config=config, **kwargs)
            
            # Create wrapped tool instance
            wrapped_tool = FilteredTool(tool, self.response_filter, self.logger)
            wrapped_tools.append(wrapped_tool)
        
        self.logger.debug(f"Wrapped {len(wrapped_tools)} tools with response filtering")
        return wrapped_tools
    
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
            
            if prompt_data["prompt"]:
                prompt_template = prompt_data["prompt"]
                self.logger.debug(f"Using Langfuse prompt {langfuse_prompt_name} v{prompt_data.get('version', 'unknown')}")
            else:
                # Fallback to local file
                prompt_template = self._get_fallback_prompt(class_name)
                prompt_data = {"prompt": prompt_template, "config": {}, "version": None, "name": langfuse_prompt_name}
        else:
            # Fallback for unmapped agents
            prompt_template = self._get_fallback_prompt(class_name)
            prompt_data = {"prompt": prompt_template, "config": {}, "version": None, "name": class_name}
        
        # Add brevity instruction if in brief mode
        if context and context.get("brevity_mode"):
            prompt_template += """

### Response Style Guidelines
For simple, straightforward questions:
- Provide a concise 2-3 sentence summary with key facts only
- Include only the most essential information
- Avoid excessive detail unless specifically requested
- Be direct and to the point

For detailed requests (containing words like "detailed", "comprehensive", "explain in depth"):
- Provide comprehensive information with all relevant details
- Include examples, citations, and thorough explanations
"""
        
        # Update prompt_data with modified template
        prompt_data["prompt"] = prompt_template
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
            
            # Add tool usage guidelines to prevent redundant calls
            system_prompt += """

### Tool Usage Guidelines - CRITICAL
- Call each tool ONCE with the best query you can formulate
- NEVER retry the same tool call with identical arguments
- If a tool returns limited data (e.g., 3 compounds), that's sufficient - work with it
- Summarize whatever information you receive, even if incomplete
- ChEMBL may not have complete data - that's normal, just report what you found
"""
            
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
                "recursion_limit": 35  # Increased from default 25 to allow more iterations
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
            
            # Invoke LangGraph agent with memory
            # Note: LangGraph's checkpointer automatically manages conversation history
            # No need to manually pass conversation_history - it's stored in the checkpoint
            result = await self.agent.ainvoke({"messages": messages}, config=config)
            
            # Extract final response from messages
            final_messages = result.get("messages", [])
            if final_messages:
                last_message = final_messages[-1]
                response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response_text = "No response generated"
            
            # Log the result (debug level for routine operations)
            messages = result.get("messages", [])
            self.logger.debug(f"{self.name} completed with {len(messages)} messages")
            
            # Log tool calls at debug level
            tool_calls_made = []
            for message in messages:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_calls_made.append({
                            'tool_name': tool_call.get('name', 'unknown'),
                            'args': tool_call.get('args', {}),
                            'id': tool_call.get('id', 'unknown')
                        })
            
            if tool_calls_made:
                self.logger.debug(f"{self.name} made {len(tool_calls_made)} tool calls: {[tc['tool_name'] for tc in tool_calls_made]}")
            
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
            
            return {
                "success": True,
                "response": response_text,
                "messages": final_messages,
                "agent": self.name,
                "tool_calls": tool_calls_made,
                "timestamp": datetime.now().isoformat()
            }
            
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
