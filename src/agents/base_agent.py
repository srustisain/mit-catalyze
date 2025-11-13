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
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Try to import Langfuse, but make it optional
try:
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    logging.warning("langfuse not available. Tracing will be disabled.")
    LangfuseCallbackHandler = None
    LANGFUSE_AVAILABLE = False


class BaseAgent(ABC):
    """Base class for all Catalyze agents"""
    
    def __init__(self, name: str, description: str, tools: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.llm_client = LLMClient(provider="openai")
        self.logger = logging.getLogger(f"catalyze.{name.lower()}")
        
        # MCP client for tool access
        self.mcp_client = None
        self.agent = None
        
        # MCP response filter to reduce token usage (50K -> 2K tokens)
        self.response_filter = MCPResponseFilter()
        
        # Initialize Langfuse callback handler
        self.langfuse_handler = None
        if LANGFUSE_AVAILABLE and LANGFUSE_ENABLED:
            try:
                self.langfuse_handler = LangfuseCallbackHandler()
                self.logger.info(f"Langfuse tracing enabled for {self.name}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Langfuse for {self.name}: {e}")
                self.langfuse_handler = None
        
    async def initialize(self):
        """Initialize the agent with MCP tools"""
        try:
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
            
            # Filter tools based on agent specialization
            if self.tools:
                available_tools = [tool for tool in available_tools if tool.name in self.tools]
            
            # Wrap tools with response filtering to reduce token usage
            available_tools = self._wrap_tools_with_filtering(available_tools)
            
            self.logger.info(f"Initialized {self.name} with {len(available_tools)} tools from {list(server_config.keys())}")
            
            # Create LangGraph agent with MCP tools if we have tools
            if available_tools and OPENAI_API_KEY:
                try:
                    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
                    # create_react_agent doesn't take state_modifier - system message passed via messages instead
                    self.agent = create_react_agent(llm, available_tools)
                    self.logger.info(f"Created LangGraph agent for {self.name} with {len(available_tools)} tools")
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
        """Wrap MCP tools with response filtering to reduce token usage"""
        from langchain_core.tools import StructuredTool
        
        wrapped_tools = []
        for tool in tools:
            # Create a wrapper function that filters the response
            original_func = tool.func if hasattr(tool, 'func') else None
            if not original_func:
                wrapped_tools.append(tool)
                continue
            
            # Create async wrapper with filtering
            async def filtered_func(*args, _original=original_func, _tool_name=tool.name, **kwargs):
                try:
                    # Call original tool
                    result = await _original(*args, **kwargs) if asyncio.iscoroutinefunction(_original) else _original(*args, **kwargs)
                    
                    # Filter response to reduce token usage
                    filtered = self.response_filter.filter_response(result, _tool_name)
                    
                    # Log filtering stats
                    original_tokens = self.response_filter.estimate_token_count(result)
                    filtered_tokens = self.response_filter.estimate_token_count(filtered)
                    if original_tokens > 1000:
                        self.logger.info(f"Filtered {_tool_name}: {original_tokens}→{filtered_tokens} tokens")
                    
                    return filtered
                except Exception as e:
                    self.logger.error(f"Tool {_tool_name} failed: {e}")
                    raise
            
            # Create new tool with same signature but filtered output
            wrapped_tool = StructuredTool(
                name=tool.name,
                description=tool.description,
                func=filtered_func,
                coroutine=filtered_func,
                args_schema=tool.args_schema if hasattr(tool, 'args_schema') else None
            )
            wrapped_tools.append(wrapped_tool)
        
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
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are {self.name}, a specialized AI agent for chemistry tasks.

{self.description}

You have access to specialized tools and databases to help with your tasks.
Always provide accurate, detailed responses and cite your sources when possible.
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
            
            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=query)
            ]
            
            # Add conversation history if available
            if context and context.get("conversation_history"):
                # Insert conversation history before the current query
                history_messages = []
                for msg in context["conversation_history"][-3:]:  # Last 3 messages for context
                    if msg.get("role") == "user":
                        history_messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        history_messages.append(AIMessage(content=msg["content"]))
                
                # Insert history between system message and current query
                messages = [messages[0]] + history_messages + [messages[1]]
            
            # Prepare config with Langfuse callbacks
            config = {"configurable": {}}
            if self.langfuse_handler:
                config["callbacks"] = [self.langfuse_handler]
                config["run_name"] = f"{self.name}_query"
                config["tags"] = [self.name, "langgraph", "mcp"]
                
                # Set session_id if available
                if context and context.get("session_id"):
                    self.langfuse_handler.session_id = context["session_id"]
            
            # Invoke LangGraph agent
            result = await self.agent.ainvoke({"messages": messages}, config=config)
            
            # Extract final response from messages
            final_messages = result.get("messages", [])
            if final_messages:
                last_message = final_messages[-1]
                response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response_text = "No response generated"
            
            return {
                "success": True,
                "response": response_text,
                "messages": final_messages,
                "agent": self.name,
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
