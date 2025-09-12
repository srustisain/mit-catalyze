#!/usr/bin/env python3
"""
Quick test for PDF processing
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.chat_endpoints import ChatEndpoints

async def test_pdf_extraction():
    """Test PDF text extraction directly"""
    print("🧪 Testing PDF Text Extraction")
    print("=" * 40)
    
    # Check if dnaprep.pdf exists
    pdf_path = "dnaprep.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ {pdf_path} not found in current directory")
        print("   Please place your PDF file in the project root")
        return
    
    print(f"📄 Found PDF: {pdf_path}")
    
    try:
        # Create chat endpoints instance
        chat_endpoints = ChatEndpoints()
        
        # Test text extraction
        print("\n🔍 Extracting text from PDF...")
        extracted_text = chat_endpoints._extract_pdf_text(pdf_path)
        
        if extracted_text:
            print(f"✅ Text extraction successful!")
            print(f"   📏 Extracted {len(extracted_text)} characters")
            print(f"\n📋 Preview (first 200 chars):")
            print("-" * 40)
            print(extracted_text[:200])
            print("-" * 40)
            
            if len(extracted_text) > 200:
                print(f"... (truncated, full text is {len(extracted_text)} characters)")
            
            # Test full PDF processing
            print(f"\n🤖 Testing full PDF processing...")
            result = await chat_endpoints.process_pdf(pdf_path, "dnaprep.pdf")
            
            if result.get('success'):
                print("✅ PDF processing successful!")
                print(f"   📄 Filename: {result.get('filename')}")
                print(f"   📏 File size: {result.get('file_size')} bytes")
                print(f"   📝 Content length: {len(result.get('content', ''))} characters")
                
                content = result.get('content', '')
                print(f"\n📋 AI Analysis Preview (first 300 chars):")
                print("-" * 50)
                print(content[:300])
                print("-" * 50)
                
                if len(content) > 300:
                    print(f"... (truncated, full analysis is {len(content)} characters)")
                    
            else:
                print(f"❌ PDF processing failed: {result.get('error')}")
        
        else:
            print("❌ No text extracted from PDF")
            print("   The PDF may be image-only or corrupted")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pdf_extraction())
