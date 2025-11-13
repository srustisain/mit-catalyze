"""
Router Agent

Intelligent router that classifies user queries and delegates to appropriate specialized agents.
Uses the SmartRouter for intelligent query classification and delegation.
"""

from typing import Dict, Any
from .smart_router import SmartRouter
from src.clients.llm_client import LLMClient

# Try to import Langfuse decorator
try:
    from langfuse.decorators import observe
except ImportError:
    # Create a no-op decorator if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])


class RouterAgent:
    """Intelligent router agent for query classification and delegation"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()
        self.smart_router = SmartRouter(llm_client)
        self.name = "RouterAgent"
    
    async def initialize_agents(self):
        """Initialize all internal agents - delegates to SmartRouter"""
        await self.smart_router.initialize_agents()
    
    @observe()
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query through the intelligent router system
        
        Args:
            query: User's query string
            context: Additional context (conversation history, etc.)
            
        Returns:
            Dictionary containing the response and metadata
        """
        # Use the smart router to process the query
        return await self.smart_router.process_query(query, context)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of the router and all agents"""
        return await self.smart_router.get_status()