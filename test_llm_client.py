#!/usr/bin/env python3
"""
Test script for LLMClient multi-provider functionality
"""

import os
import sys
from llm_client import LLMClient

def test_llm_client():
    """Test LLMClient with different providers"""
    
    # Test with default provider (from config)
    print("Testing LLMClient with default provider...")
    client = LLMClient()
    print(f"Default provider: {client.provider}")
    
    # Test provider switching
    print("\nTesting provider switching...")
    
    # Test OpenAI provider
    client.set_provider("openai")
    print(f"Switched to provider: {client.provider}")
    
    # Test Cerebras provider
    client.set_provider("cerebras")
    print(f"Switched to provider: {client.provider}")
    
    # Test Hugging Face provider
    client.set_provider("huggingface")
    print(f"Switched to provider: {client.provider}")
    
    print("\nLLMClient multi-provider setup complete!")
    print("Make sure to configure your API keys in the .env file.")

if __name__ == "__main__":
    test_llm_client()
