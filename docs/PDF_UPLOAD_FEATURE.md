# 📄 PDF Upload Feature Documentation

## Overview

The Catalyze application now supports PDF upload functionality that allows users to upload scientific PDFs and ask questions about their content. The system uses OpenAI's GPT-4o model to analyze PDF documents and integrate the extracted information into chat responses.

## Features

### 🚀 Core Functionality
- **PDF Upload**: Drag-and-drop or click-to-browse PDF upload interface
- **AI Analysis**: OpenAI GPT-4o extracts and summarizes PDF content
- **Context Integration**: PDF content is automatically included in chat responses
- **Multi-Agent Support**: All agents (Research, Protocol, Safety, Automate) can use PDF context
- **Visual Indicators**: Clear UI feedback showing when PDF context is active

### 🛡️ Security & Validation
- **File Type Validation**: Only PDF files are accepted
- **File Size Limit**: Maximum 10MB file size
- **Secure Processing**: Temporary files are cleaned up after processing
- **Error Handling**: Comprehensive error handling with user-friendly messages

## User Interface

### Upload Interface
- **Upload Button**: Blue 📄 button in the chat input area
- **Drag & Drop**: Users can drag PDF files directly onto the upload area
- **Progress Indicator**: Real-time upload and processing progress
- **Success/Error Feedback**: Clear visual feedback for upload status

### Chat Integration
- **Context Indicator**: Shows when PDF is being analyzed in responses
- **Filename Display**: Shows the name of the currently loaded PDF
- **Clear Context**: Button to clear PDF context and return to normal chat

## Technical Implementation

### Frontend (HTML/JavaScript)
```javascript
// PDF Upload Functions
function togglePdfUpload()        // Show/hide upload interface
function uploadPdf(file)          // Handle file upload
function clearPdfContext()        // Clear PDF context
function setupDragAndDrop()       // Drag & drop functionality
```

### Backend (Python/Flask)
```python
# API Endpoints
POST /api/upload-pdf              # Upload and process PDF
POST /api/chat                    # Chat with PDF context

# Key Classes
ChatEndpoints.process_pdf()       # PDF processing with OpenAI
BaseAgent.process_query()         # Enhanced with PDF context
```

### Agent Integration
All agents now support PDF context:
- **Research Agent**: Incorporates PDF findings into research responses
- **Protocol Agent**: Uses PDF methodologies for protocol generation
- **Safety Agent**: Analyzes PDF safety information
- **Automate Agent**: References PDF procedures for automation

## API Endpoints

### Upload PDF
```
POST /api/upload-pdf
Content-Type: multipart/form-data

Parameters:
- pdf: PDF file (required, max 10MB)

Response:
{
  "success": true,
  "filename": "document.pdf",
  "content": "Extracted text content...",
  "file_size": 1024000,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Chat with PDF Context
```
POST /api/chat
Content-Type: application/json

Body:
{
  "message": "What is the main finding?",
  "mode": "research",
  "conversation_history": [],
  "pdf_context": {
    "filename": "document.pdf",
    "content": "PDF content...",
    "upload_time": "2024-01-01T12:00:00Z",
    "file_size": 1024000
  }
}
```

## Usage Examples

### 1. Upload a Scientific Paper
1. Click the 📄 button in the chat interface
2. Drag and drop or select a PDF file
3. Wait for processing to complete
4. Ask questions about the document

### 2. Research Questions
```
User: "What are the key findings in this paper?"
Agent: [Analyzes PDF content and provides comprehensive summary]

User: "Can you explain the methodology used?"
Agent: [References specific methods from the PDF]
```

### 3. Protocol Generation
```
User: "Generate a protocol based on the synthesis method in the paper"
Agent: [Creates detailed protocol incorporating PDF procedures]
```

## Error Handling

### Common Errors
- **File too large**: "File size must be less than 10MB"
- **Invalid format**: "File must be a PDF"
- **Processing failure**: "Failed to process PDF: [reason]"
- **Empty file**: "PDF file is empty"

### Recovery
- Users can retry uploads after fixing issues
- Clear PDF context button resets the interface
- Graceful fallback to normal chat if PDF processing fails

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your-openai-api-key  # Required for PDF processing
```

### File Limits
- Maximum file size: 10MB
- Supported formats: PDF only
- Processing timeout: 60 seconds

## Testing

### Test Script
Run the included test script to verify functionality:
```bash
python test_pdf_upload.py
```

### Manual Testing
1. Start the Flask application
2. Open http://localhost:5003
3. Upload a test PDF
4. Ask questions about the content

## Performance Considerations

### Optimization
- Temporary files are cleaned up immediately after processing
- PDF content is cached in memory during chat session
- OpenAI API calls have 60-second timeout
- File size limit prevents memory issues

### Limitations
- Large PDFs (>10MB) are rejected
- Complex PDFs with many images may take longer to process
- PDF content is limited to 4000 tokens in OpenAI response

## Future Enhancements

### Planned Features
- **Multiple PDF Support**: Upload and analyze multiple documents
- **PDF Annotation**: Highlight and annotate PDF content
- **Export Results**: Save analysis results to file
- **Batch Processing**: Process multiple PDFs simultaneously
- **Advanced Search**: Search within PDF content

### Technical Improvements
- **Caching**: Cache processed PDF content for faster access
- **Compression**: Compress large PDFs before processing
- **Async Processing**: Background PDF processing
- **Database Storage**: Store PDF metadata and content

## Troubleshooting

### Common Issues

#### PDF Upload Fails
- Check file size (must be < 10MB)
- Verify file is a valid PDF
- Ensure OpenAI API key is configured

#### Processing Errors
- Check OpenAI API key validity
- Verify internet connection
- Try with a simpler PDF

#### Chat Integration Issues
- Clear PDF context and retry
- Check browser console for JavaScript errors
- Verify Flask application is running

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues or questions about the PDF upload feature:
1. Check the error messages in the UI
2. Review the Flask application logs
3. Run the test script to verify functionality
4. Check OpenAI API key configuration

---

**Note**: This feature requires an active OpenAI API key and internet connection for PDF processing.
