#!/usr/bin/env python3
"""
Test script for PDF upload functionality
"""

import requests
import os
import tempfile
from pathlib import Path

def create_test_pdf():
    """Create a simple test PDF for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        
        # Create a simple PDF with test content
        c = canvas.Canvas(temp_file.name, pagesize=letter)
        c.drawString(100, 750, "Test Scientific Document")
        c.drawString(100, 720, "This is a test PDF for the Catalyze PDF upload feature.")
        c.drawString(100, 690, "It contains basic chemistry information:")
        c.drawString(100, 660, "- Molecular formula: H2O")
        c.drawString(100, 630, "- Molecular weight: 18.015 g/mol")
        c.drawString(100, 600, "- Boiling point: 100°C at 1 atm")
        c.drawString(100, 570, "- This is a simple test to verify PDF processing.")
        c.save()
        
        return temp_file.name
        
    except ImportError:
        print("reportlab not available, creating a simple text file instead")
        # Create a simple text file as fallback
        temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w')
        temp_file.write("Test Scientific Document\n")
        temp_file.write("This is a test document for the Catalyze PDF upload feature.\n")
        temp_file.write("It contains basic chemistry information:\n")
        temp_file.write("- Molecular formula: H2O\n")
        temp_file.write("- Molecular weight: 18.015 g/mol\n")
        temp_file.write("- Boiling point: 100°C at 1 atm\n")
        temp_file.write("- This is a simple test to verify document processing.\n")
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
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ PDF upload successful!")
                print(f"   📄 Filename: {data.get('filename')}")
                print(f"   📊 File size: {data.get('file_size')} bytes")
                print(f"   📝 Content length: {len(data.get('content', ''))} characters")
                print(f"   ⏰ Timestamp: {data.get('timestamp')}")
                print("\n📋 Extracted content preview:")
                content = data.get('content', '')
                print(content[:200] + "..." if len(content) > 200 else content)
                return True
            else:
                print(f"❌ PDF processing failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Upload timed out (60 seconds)")
        return False
    except Exception as e:
        print(f"❌ Upload failed with error: {e}")
        return False
    finally:
        # Clean up test file
        try:
            os.unlink(test_file)
            print(f"\n🧹 Cleaned up test file: {test_file}")
        except:
            pass

def test_chat_with_pdf():
    """Test chat functionality with PDF context"""
    print("\n💬 Testing Chat with PDF Context")
    print("=" * 50)
    
    # First upload a PDF
    test_file = create_test_pdf()
    
    try:
        # Upload PDF
        with open(test_file, 'rb') as f:
            files = {'pdf': f}
            response = requests.post(
                "http://localhost:5003/api/upload-pdf",
                files=files,
                timeout=60
            )
        
        if response.status_code != 200 or not response.json().get('success'):
            print("❌ PDF upload failed, cannot test chat with PDF")
            return False
        
        pdf_data = response.json()
        
        # Test chat with PDF context
        print("\n💬 Testing chat with PDF context...")
        chat_data = {
            "message": "What is the molecular formula mentioned in the document?",
            "mode": "research",
            "conversation_history": [],
            "pdf_context": {
                "filename": pdf_data.get('filename'),
                "content": pdf_data.get('content'),
                "upload_time": pdf_data.get('timestamp'),
                "file_size": pdf_data.get('file_size')
            }
        }
        
        response = requests.post(
            "http://localhost:5003/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Chat with PDF context successful!")
                print(f"   🤖 Agent used: {data.get('agent_used')}")
                print(f"   📄 PDF context: {data.get('agent_used', 'Unknown')} agent")
                print(f"   📝 Response length: {len(data.get('response', ''))} characters")
                print("\n💬 Response preview:")
                response_text = data.get('response', '')
                print(response_text[:300] + "..." if len(response_text) > 300 else response_text)
                return True
            else:
                print(f"❌ Chat failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Chat request failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat test failed with error: {e}")
        return False
    finally:
        # Clean up test file
        try:
            os.unlink(test_file)
        except:
            pass

if __name__ == "__main__":
    print("🧪 Catalyze PDF Upload Test Suite")
    print("=" * 60)
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set")
        print("   PDF processing will fail without this key")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print()
    
    # Run tests
    pdf_test_passed = test_pdf_upload()
    
    if pdf_test_passed:
        chat_test_passed = test_chat_with_pdf()
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print(f"   📄 PDF Upload: {'✅ PASSED' if pdf_test_passed else '❌ FAILED'}")
        print(f"   💬 Chat with PDF: {'✅ PASSED' if chat_test_passed else '❌ FAILED'}")
        
        if pdf_test_passed and chat_test_passed:
            print("\n🎉 All tests passed! PDF upload functionality is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the error messages above.")
    else:
        print("\n❌ PDF upload test failed. Cannot proceed with chat test.")
    
    print("\n🚀 To test manually:")
    print("   1. Start the Flask app: python app/flask_app.py")
    print("   2. Open http://localhost:5003 in your browser")
    print("   3. Click the 📄 button to upload a PDF")
    print("   4. Ask questions about the uploaded PDF")
