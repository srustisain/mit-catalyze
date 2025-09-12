import sys 
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import Dict, List
import json
from datetime import datetime
import asyncio
import tempfile
from werkzeug.utils import secure_filename

from src.api import ChatEndpoints
from src.config.logging_config import get_logger

# Get logger
logger = get_logger("catalyze.flask")

app = Flask(__name__, static_folder='../react-build', static_url_path='')
CORS(app)

# Initialize chat endpoints
chat_endpoints = ChatEndpoints()

@app.route('/')
def serve_react_app():
    """Serve the React app"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Catalyze API is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def chat_with_llm():
    """Chat with LLM using agent-based processing"""
    try:
        data = request.get_json()
        
        # Validate request
        is_valid, error_msg = chat_endpoints.validate_request(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        message = data.get('message', '').strip()
        mode = data.get('mode', 'research')  # Get mode from frontend
        conversation_history = data.get('conversation_history', [])
        pdf_context = data.get('pdf_context', None)  # Get PDF context if available
        
        logger.info(f"Processing chat message in {mode} mode: {message[:50]}...")
        
        # Process the message asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                chat_endpoints.process_chat_message(
                    message=message,
                    mode=mode,
                    conversation_history=conversation_history,
                    pdf_context=pdf_context
                )
            )
            
            logger.info(f"Chat processed successfully by {result.get('agent_used', 'unknown')} agent")
            
            return jsonify({
                'response': result.get('response', 'No response generated'),
                'timestamp': result.get('timestamp', datetime.now().isoformat()),
                'used_mcp': result.get('used_mcp', False),
                'agent_used': result.get('agent_used', mode),
                'mode': result.get('mode', mode),
                'success': result.get('success', True)
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({
            'error': f'Error processing chat: {str(e)}',
            'response': 'Sorry, I encountered an error processing your request. Please try again.',
            'timestamp': datetime.now().isoformat(),
            'success': False
        }), 500

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get information about available agents"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            agents_info = loop.run_until_complete(chat_endpoints.get_agent_info())
            return jsonify(agents_info)
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Agents endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get pipeline status"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            status = loop.run_until_complete(chat_endpoints.get_pipeline_status())
            return jsonify(status)
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    """Upload and process PDF files"""
    temp_path = None
    temp_dir = None
    
    try:
        # Check if file is present
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'error': 'No PDF file provided'}), 400
        
        file = request.files['pdf']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file extension
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'File must be a PDF'}), 400
        
        # Check file size (limit to 10MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({'success': False, 'error': 'File size must be less than 10MB'}), 400
        
        if file_size == 0:
            return jsonify({'success': False, 'error': 'File is empty'}), 400
        
        # Create temporary file
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"upload_{int(time.time())}.pdf"
        
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        logger.info(f"PDF uploaded: {filename} ({file_size} bytes)")
        
        # Process PDF with OpenAI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                chat_endpoints.process_pdf(temp_path, filename)
            )
            
            # Ensure result has success field
            if 'success' not in result:
                result['success'] = True
            
            return jsonify(result)
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"PDF upload error: {e}")
        return jsonify({'success': False, 'error': f'Failed to process PDF: {str(e)}'}), 500
    
    finally:
        # Clean up temporary files
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_path}: {e}")
        
        if temp_dir and os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to remove temp directory {temp_dir}: {e}")

@app.route('/api/opentrons-status', methods=['GET'])
def get_opentrons_status():
    """Get Opentrons generation status (placeholder for future WebSocket implementation)"""
    return jsonify({
        'status': 'idle',
        'message': 'Opentrons generator ready',
        'timestamp': datetime.now().isoformat()
    })

# Serve static files
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    logger.info("Starting Catalyze Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5003)