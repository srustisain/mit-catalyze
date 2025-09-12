#!/usr/bin/env python3
"""
Simple test for PDF upload functionality
"""

import requests
import os

def test_pdf_upload():
    """Test PDF upload with a simple text file"""
    print("🧪 Testing PDF Upload Functionality")
    print("=" * 40)
    
    # Create a simple test file
    test_content = """
    Test Scientific Document: DNA Preparation Protocol
    
    Abstract:
    This document describes a protocol for DNA extraction and preparation for sequencing applications.
    
    Materials:
    - Sample DNA
    - Buffer solution
    - Centrifuge
    - Pipettes
    
    Procedure:
    1. Add 100μL of buffer to the sample
    2. Mix thoroughly
    3. Centrifuge at 3000 rpm for 5 minutes
    4. Collect supernatant
    
    Results:
    The protocol yields high-quality DNA suitable for PCR amplification.
    
    Conclusion:
    This method provides reliable DNA preparation for downstream applications.
    """
    
    # Create a temporary text file (simulating a PDF)
    with open("test_document.txt", "w") as f:
        f.write(test_content)
    
    print("📄 Created test document")
    
    # Test the chat endpoint without PDF first
    print("\n💬 Testing regular chat...")
    chat_data = {
        "message": "Hello, can you help me with chemistry?",
        "mode": "research",
        "conversation_history": []
    }
    
    try:
        response = requests.post(
            "http://localhost:5003/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Regular chat working!")
            print(f"   Agent: {data.get('agent_used')}")
            print(f"   Response length: {len(data.get('response', ''))}")
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"   Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
    
    # Clean up
    os.remove("test_document.txt")
    
    print("\n🎯 Next Steps:")
    print("1. Open http://localhost:5003 in your browser")
    print("2. Click the 📄 button to upload your PDF")
    print("3. Upload your 'dnaprep.pdf' file")
    print("4. Ask questions about the document")

if __name__ == "__main__":
    test_pdf_upload()
