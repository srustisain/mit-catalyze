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
from src.config.config import OPENAI_MODEL, MCP_SERVERS
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


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
        
    async def initialize(self):
        """Initialize the agent with MCP tools"""
        try:
            if not MCP_SERVERS:
                self.logger.warning(f"No MCP servers configured, initializing {self.name} without tools")
                self.mcp_client = None
                self.agent = None
                return
            
            self.mcp_client = MultiServerMCPClient(MCP_SERVERS)
            all_tools = await self.mcp_client.get_tools()
            
            # Filter tools based on agent specialization
            if self.tools:
                available_tools = [tool for tool in all_tools if tool.name in self.tools]
            else:
                available_tools = all_tools[:3]  # Limit to 3 tools to avoid context issues
            
            # Further limit tools to prevent context overflow
            available_tools = available_tools[:2]  # Maximum 2 tools per agent
            
            self.logger.info(f"Initialized {self.name} with {len(available_tools)} tools")
            
            # Create LangGraph agent
            self.agent = create_react_agent(OPENAI_MODEL, available_tools)
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize {self.name} with MCP tools: {e}")
            self.logger.info(f"Initializing {self.name} without tools as fallback")
            self.mcp_client = None
            self.agent = None
    
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
            
            # Prepare the input for the agent
            agent_input = {
                "messages": [
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": query}
                ]
            }
            
            # Add context if provided
            if context:
                agent_input["context"] = context
            
            # Run the agent
            result = await self.agent.ainvoke(agent_input)
            
            return {
                "success": True,
                "response": result.get("messages", []),
                "agent": self.name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {e}")
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
