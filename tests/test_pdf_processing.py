#!/usr/bin/env python3
"""
Debug script for PDF processing issues
"""

import requests
import json
import os

def test_pdf_upload_debug():
    """Test PDF upload with detailed debugging"""
    print("🔍 Debugging PDF Upload Processing")
    print("=" * 50)
    
    # Check server status
    try:
        response = requests.get("http://localhost:5003/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not running. Start with: python app/flask_app.py")
            return
        print("✅ Server is running")
    except:
        print("❌ Cannot connect to server")
        return
    
    # Check if you have a test PDF
    test_files = [
        "dnaprep.pdf",  # Your actual file
        "test.pdf",
        "sample.pdf"
    ]
    
    pdf_path = None
    for file in test_files:
        if os.path.exists(file):
            pdf_path = file
            break
    
    if not pdf_path:
        print("❌ No test PDF found. Please place 'dnaprep.pdf' in the current directory")
        print("   Or create a test PDF file")
        return
    
    print(f"📄 Found test PDF: {pdf_path}")
    
    # Upload PDF
    try:
        print("\n🚀 Uploading PDF...")
        with open(pdf_path, 'rb') as f:
            files = {'pdf': f}
            response = requests.post(
                "http://localhost:5003/api/upload-pdf",
                files=files,
                timeout=60
            )
        
        print(f"📊 Upload Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful: {data.get('success')}")
            print(f"📄 Filename: {data.get('filename')}")
            print(f"📏 File size: {data.get('file_size')} bytes")
            print(f"📝 Content length: {len(data.get('content', ''))} characters")
            
            # Show content preview
            content = data.get('content', '')
            print(f"\n📋 Content Preview (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            
            if len(content) > 500:
                print(f"... (truncated, full content is {len(content)} characters)")
            
            # Test chat with PDF
            print(f"\n💬 Testing chat with PDF context...")
            chat_data = {
                "message": "Please summarize the key points from this document",
                "mode": "research",
                "conversation_history": [],
                "pdf_context": {
                    "filename": data.get('filename'),
                    "content": data.get('content'),
                    "upload_time": data.get('timestamp'),
                    "file_size": data.get('file_size')
                }
            }
            
            chat_response = requests.post(
                "http://localhost:5003/api/chat",
                json=chat_data,
                timeout=30
            )
            
            print(f"📊 Chat Response Status: {chat_response.status_code}")
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                print(f"✅ Chat successful: {chat_data.get('success')}")
                print(f"🤖 Agent used: {chat_data.get('agent_used')}")
                
                response_text = chat_data.get('response', '')
                print(f"\n💬 Chat Response Preview:")
                print("-" * 50)
                print(response_text[:800])
                print("-" * 50)
                
                if len(response_text) > 800:
                    print(f"... (truncated, full response is {len(response_text)} characters)")
                
                # Check for issues
                if "system" in response_text.lower() and "prompt" in response_text.lower():
                    print("\n⚠️  WARNING: Response contains system prompt text")
                    print("   This suggests the agent is not properly filtering responses")
                
                if "ChEMBL Database:" in response_text:
                    print("\n⚠️  WARNING: ChEMBL enhancement may be interfering with PDF processing")
                
            else:
                print(f"❌ Chat failed: {chat_response.status_code}")
                print(f"   Error: {chat_response.text}")
        
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def check_environment():
    """Check environment setup"""
    print("🔧 Environment Check")
    print("=" * 30)
    
    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"✅ OPENAI_API_KEY: Set (length: {len(api_key)})")
    else:
        print("❌ OPENAI_API_KEY: Not set")
        print("   Set with: export OPENAI_API_KEY='your-key-here'")
    
    # Check Python packages
    try:
        import openai
        print("✅ OpenAI package: Available")
    except ImportError:
        print("❌ OpenAI package: Not installed")
        print("   Install with: pip install openai")
    
    try:
        import requests
        print("✅ Requests package: Available")
    except ImportError:
        print("❌ Requests package: Not installed")

if __name__ == "__main__":
    print("🔍 PDF Processing Debug Tool")
    print("=" * 60)
    
    check_environment()
    print()
    test_pdf_upload_debug()
    
    print("\n" + "=" * 60)
    print("📋 Troubleshooting Tips:")
    print("1. Ensure Flask app is running: python app/flask_app.py")
    print("2. Check OpenAI API key is set and valid")
    print("3. Verify PDF file is not corrupted or password-protected")
    print("4. Check Flask logs for detailed error messages")
    print("5. Try with a simpler PDF first")
