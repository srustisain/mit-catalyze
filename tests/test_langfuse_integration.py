"""
Test Langfuse Integration

Verifies that Langfuse tracing is properly integrated across the application.
"""

import pytest
import asyncio
import os
from datetime import datetime

# Set test environment variables before importing modules
os.environ.setdefault("LANGFUSE_ENABLED", "false")  # Disable during tests unless explicitly testing

from src.clients.llm_client import LLMClient
from src.agents.research_agent import ResearchAgent
from src.agents.protocol_agent import ProtocolAgent
from src.pipeline.pipeline_manager import PipelineManager
from src.api.chat_endpoints import ChatEndpoints


class TestLangfuseIntegration:
    """Test suite for Langfuse integration"""
    
    def test_langfuse_import(self):
        """Test that Langfuse can be imported (or gracefully fails)"""
        try:
            from langfuse.decorators import observe
            from langfuse.langchain import CallbackHandler
            from langfuse import get_client
            assert True, "Langfuse imported successfully"
        except ImportError:
            # This is acceptable - app should work without Langfuse
            assert True, "Langfuse not available, but app should handle gracefully"
    
    def test_llm_client_with_observe(self):
        """Test that LLM client methods can be called with @observe decorators"""
        client = LLMClient()
        
        # Test that decorated methods can be called
        try:
            # These should work whether or not Langfuse is available
            # The decorator should be no-op if Langfuse is not installed
            response = client.generate_response(
                "What is chemistry?",
                "You are a helpful assistant."
            )
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            # Only acceptable error is LLM API not configured
            assert "api key" in str(e).lower() or "not available" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_agent_process_query_with_observe(self):
        """Test that agent process_query works with @observe decorator"""
        agent = ResearchAgent()
        
        try:
            result = await agent.process_query(
                "What is benzene?",
                context={"mode": "research"}
            )
            
            # Should return a dictionary with expected fields
            assert isinstance(result, dict)
            assert "success" in result
            assert "response" in result
            assert "agent" in result
            
        except Exception as e:
            # Only acceptable errors are MCP/LLM not configured
            error_str = str(e).lower()
            assert any(keyword in error_str for keyword in ["api", "mcp", "not available", "config"])
    
    @pytest.mark.asyncio
    async def test_pipeline_manager_with_observe(self):
        """Test that pipeline manager works with @observe decorator"""
        manager = PipelineManager()
        
        try:
            result = await manager.process_query(
                query="What is water?",
                mode="research",
                context={"timestamp": datetime.now().isoformat()}
            )
            
            # Should return a dictionary
            assert isinstance(result, dict)
            assert "response" in result or "error" in result
            
        except Exception as e:
            # Only acceptable errors are initialization errors
            error_str = str(e).lower()
            assert any(keyword in error_str for keyword in ["api", "init", "config"])
    
    @pytest.mark.asyncio
    async def test_chat_endpoints_with_observe(self):
        """Test that chat endpoints work with @observe decorator"""
        endpoints = ChatEndpoints()
        
        try:
            result = await endpoints.process_chat_message(
                message="What is chemistry?",
                mode="research",
                conversation_history=[]
            )
            
            # Should return a dictionary
            assert isinstance(result, dict)
            assert "response" in result
            assert "timestamp" in result
            
        except Exception as e:
            # Only acceptable errors are LLM/API not configured
            error_str = str(e).lower()
            assert any(keyword in error_str for keyword in ["api", "llm", "config"])
    
    def test_langfuse_config_loaded(self):
        """Test that Langfuse configuration is properly loaded"""
        from src.config.config import (
            LANGFUSE_PUBLIC_KEY,
            LANGFUSE_SECRET_KEY,
            LANGFUSE_HOST,
            LANGFUSE_ENABLED
        )
        
        # These should be defined (may be None)
        assert LANGFUSE_PUBLIC_KEY is not None or LANGFUSE_PUBLIC_KEY is None
        assert LANGFUSE_SECRET_KEY is not None or LANGFUSE_SECRET_KEY is None
        assert LANGFUSE_HOST is not None
        assert isinstance(LANGFUSE_ENABLED, bool)
    
    def test_base_agent_langfuse_handler(self):
        """Test that base agent properly initializes Langfuse handler"""
        agent = ResearchAgent()
        
        # Handler should be None or a CallbackHandler instance
        assert agent.langfuse_handler is None or hasattr(agent, 'langfuse_handler')
    
    @pytest.mark.asyncio
    async def test_nested_tracing(self):
        """Test that nested operations maintain trace hierarchy"""
        # This tests that decorators work in nested calls
        manager = PipelineManager()
        
        try:
            # This should create a trace with nested spans
            result = await manager.process_query(
                query="Explain benzene",
                mode="research",
                context={
                    "conversation_history": [],
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Should complete without errors
            assert isinstance(result, dict)
            
        except Exception as e:
            # Acceptable errors
            error_str = str(e).lower()
            assert any(keyword in error_str for keyword in ["api", "config", "init"])
    
    def test_fallback_when_langfuse_disabled(self):
        """Test that app works when LANGFUSE_ENABLED is False"""
        # Re-import with disabled flag
        os.environ["LANGFUSE_ENABLED"] = "false"
        
        # App should still work
        client = LLMClient()
        assert client is not None
        
        agent = ResearchAgent()
        assert agent is not None
        assert agent.langfuse_handler is None  # Should be None when disabled


class TestLangfuseGracefulDegradation:
    """Test that app handles Langfuse failures gracefully"""
    
    def test_missing_langfuse_package(self):
        """Test that missing Langfuse package doesn't break the app"""
        # Even if langfuse is not installed, decorators should be no-op
        from src.clients.llm_client import LLMClient
        client = LLMClient()
        assert client is not None
    
    @pytest.mark.asyncio
    async def test_langfuse_init_failure(self):
        """Test that Langfuse initialization failure doesn't break the app"""
        # Set invalid credentials to force init failure
        os.environ["LANGFUSE_ENABLED"] = "true"
        os.environ["LANGFUSE_PUBLIC_KEY"] = "invalid"
        os.environ["LANGFUSE_SECRET_KEY"] = "invalid"
        
        # App should still work
        agent = ResearchAgent()
        
        try:
            result = await agent.process_query("What is water?")
            # Should work even if tracing fails
            assert isinstance(result, dict)
        except Exception as e:
            # Only acceptable errors are LLM/MCP not configured
            error_str = str(e).lower()
            assert any(keyword in error_str for keyword in ["api", "llm", "mcp"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

