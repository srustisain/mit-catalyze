#!/usr/bin/env python3
"""
Simple test script to verify LLM integration works
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_llm_integration():
    """Test the LLM client directly"""
    try:
        from clients.llm_client import LLMClient
        
        print("✅ Successfully imported LLMClient")
        
        # Initialize client with OpenAI
        client = LLMClient(provider="openai")
        print(f"✅ Initialized LLM client with provider: {client.provider}")
        
        # Test simple chat response
        print("🤖 Testing chat response...")
        response = client.generate_chat_response("Hello! Can you tell me about chemistry?")
        
        print(f"✅ LLM Response: {response}")
        print("\n🎉 LLM integration is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM integration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing LLM Integration...")
    print(f"OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'Not set')}")
    print("-" * 50)
    
    success = test_llm_integration()
    
    if success:
        print("\n✅ All tests passed! Your LLM integration is ready.")
    else:
        print("\n❌ Tests failed. Please check the configuration.")
