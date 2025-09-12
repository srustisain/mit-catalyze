#!/usr/bin/env python3
"""
Test PDF processing functionality directly
"""

import tempfile
import os
import asyncio
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.chat_endpoints import ChatEndpoints

def create_test_pdf():
    """Create a simple test PDF file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    
    # Create a simple PDF with some text
    c = canvas.Canvas(temp_file.name, pagesize=letter)
    c.drawString(100, 750, "Test Scientific Document")
    c.drawString(100, 700, "This is a test PDF for the Catalyze application.")
    c.drawString(100, 650, "It contains some sample scientific content.")
    c.drawString(100, 600, "Chemical Formula: H2O")
    c.drawString(100, 550, "Molecular Weight: 18.015 g/mol")
    c.drawString(100, 500, "This document tests the PDF upload functionality.")
    c.drawString(100, 450, "Safety Information: Handle with care.")
    c.drawString(100, 400, "Experimental Procedure: Mix 1:1 ratio.")
    c.save()
    temp_file.close()
    
    return temp_file.name

async def test_pdf_processing():
    """Test PDF processing directly"""
    print("🧪 Testing PDF Processing Functionality")
    print("=" * 50)
    
    # Create test PDF
    print("\n📄 Creating test PDF...")
    test_file = create_test_pdf()
    print(f"✅ Test file created: {test_file}")
    
    try:
        # Initialize chat endpoints
        print("\n🔧 Initializing ChatEndpoints...")
        chat_endpoints = ChatEndpoints()
        
        # Test PDF processing
        print("\n🚀 Testing PDF processing...")
        result = await chat_endpoints.process_pdf(test_file, "test_document.pdf")
        
        print(f"📊 Processing Result:")
        print(f"  Success: {result.get('success')}")
        print(f"  Filename: {result.get('filename')}")
        print(f"  File size: {result.get('file_size')} bytes")
        print(f"  Content length: {len(result.get('content', ''))} characters")
        
        if result.get('success'):
            content = result.get('content', '')
            print(f"\n📋 Content Preview (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            
            if len(content) > 500:
                print(f"... (truncated, full content is {len(content)} characters)")
            
            print("\n✅ PDF processing test completed successfully!")
            return True
        else:
            print(f"❌ PDF processing failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test file
        try:
            os.unlink(test_file)
            print(f"\n🧹 Cleaned up test file: {test_file}")
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_pdf_processing())
    if success:
        print("\n🎉 PDF processing test completed successfully!")
    else:
        print("\n💥 PDF processing test failed!")