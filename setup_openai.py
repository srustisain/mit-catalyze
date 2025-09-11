#!/usr/bin/env python3
"""
Setup script for OpenAI API key configuration
Run this script to set up your OpenAI API key for the Catalyze app
"""

import os
import sys
from pathlib import Path

def setup_openai_key():
    """Interactive setup for OpenAI API key"""
    print("🔧 OpenAI API Key Setup for Catalyze")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        with open(env_file, 'r') as f:
            content = f.read()
            if "OPENAI_API_KEY=" in content and "your_openai_api_key_here" not in content:
                print("✅ OpenAI API key appears to be configured")
                return True
    else:
        print("❌ .env file not found")
    
    print("\n📝 To set up your OpenAI API key:")
    print("1. Get your API key from: https://platform.openai.com/api-keys")
    print("2. Create a .env file in the project root with:")
    print("   OPENAI_API_KEY=your_actual_api_key_here")
    print("   LLM_PROVIDER=openai")
    print("   OPENAI_MODEL=gpt-3.5-turbo")
    
    # Try to set environment variable for current session
    api_key = input("\n🔑 Enter your OpenAI API key (or press Enter to skip): ").strip()
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["OPENAI_MODEL"] = "gpt-3.5-turbo"
        
        print("✅ Environment variables set for current session")
        print("💡 For permanent setup, create a .env file as described above")
        return True
    else:
        print("⚠️  Skipped API key setup")
        return False

def test_openai_connection():
    """Test OpenAI connection"""
    try:
        from src.clients.llm_client import LLMClient
        
        print("\n🧪 Testing OpenAI connection...")
        llm_client = LLMClient(provider="openai")
        
        # Test with a simple message
        response = llm_client.generate_chat_response("Hello, can you respond with 'Connection successful!'?")
        
        if response and "Connection successful" in response:
            print("✅ OpenAI connection successful!")
            print(f"🤖 Response: {response}")
            return True
        else:
            print("⚠️  Unexpected response from OpenAI")
            print(f"🤖 Response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Catalyze OpenAI Setup")
    print("=" * 30)
    
    # Setup API key
    if setup_openai_key():
        # Test connection
        test_openai_connection()
    else:
        print("\n💡 You can run this script again anytime to set up your API key")
        print("   Or manually create a .env file with your OpenAI API key")
    
    print("\n🎉 Setup complete! You can now run your Flask app:")
    print("   python app/flask_app.py")
