#!/usr/bin/env python3
"""
Simple test script for PDF upload functionality
"""

import requests
import tempfile
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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
    c.save()
    temp_file.close()
    
    return temp_file.name

def test_pdf_upload():
    """Test the PDF upload endpoint"""
    print("🧪 Testing PDF Upload Functionality")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5003/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running. Please start the Flask app first.")
            return False
        print("✅ Server is running")
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Please start the Flask app first.")
        return False
    
    # Create test PDF
    print("\n📄 Creating test PDF...")
    test_file = create_test_pdf()
    print(f"✅ Test file created: {test_file}")
    
    try:
        # Test PDF upload
        print("\n🚀 Testing PDF upload...")
        with open(test_file, 'rb') as f:
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
            
            return True
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Clean up test file
        try:
            os.unlink(test_file)
            print(f"\n🧹 Cleaned up test file: {test_file}")
        except:
            pass

if __name__ == "__main__":
    success = test_pdf_upload()
    if success:
        print("\n🎉 PDF upload test completed successfully!")
    else:
        print("\n💥 PDF upload test failed!")

