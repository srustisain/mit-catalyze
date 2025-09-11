import sys 
sys.path.insert(0, '.')

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from typing import Dict, List
import json
from datetime import datetime
import re

from src.pipeline import run_pipeline

app = Flask(__name__, static_folder='../react-build', static_url_path='')
CORS(app)

# In-memory storage for conversation history (in production, use a database)
conversation_history = []

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

@app.route('/api/query', methods=['POST'])
def process_chemistry_query():
    """Process a chemistry query and return results"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        explain_mode = data.get('explain_mode', False)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Delegate the entire workflow to the new LangGraph‑based pipeline.
        # The pipeline handles chemical extraction, PubChem lookup,
        # MCP tool orchestration, automation script generation, and
        # response assembly.
        response = run_pipeline(query, explain_mode=explain_mode)

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
def get_conversation_history():
    """Get conversation history"""
    return jsonify({
        'history': conversation_history,
        'total': len(conversation_history)
    })

@app.route('/api/history/<int:history_id>', methods=['GET'])
def get_specific_conversation(history_id):
    """Get a specific conversation by ID"""
    for conv in conversation_history:
        if conv['id'] == history_id:
            return jsonify(conv)
    return jsonify({'error': 'Conversation not found'}), 404

@app.route('/api/clear-history', methods=['POST'])
def clear_conversation_history():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return jsonify({'message': 'History cleared successfully'})

@app.route('/api/demo-queries', methods=['GET'])
def get_demo_queries():
    """Get demo queries for the frontend"""
    return jsonify({
        'queries': [
            {
                'id': 1,
                'query': 'Synthesize benzyl alcohol from benzyl chloride',
                'description': 'Classic SN2 substitution reaction',
                'category': 'synthesis'
            },
            {
                'id': 2,
                'query': 'Which solid electrolytes are stable above 60°C?',
                'description': 'Materials science query',
                'category': 'materials'
            },
            {
                'id': 3,
                'query': 'Top perovskites with band gap 1.3-1.7 eV',
                'description': 'Photovoltaic materials',
                'category': 'materials'
            },
            {
                'id': 4,
                'query': 'Greener solvent replacements for DMF',
                'description': 'Green chemistry focus',
                'category': 'green_chemistry'
            }
        ]
    })

@app.route('/api/download-script', methods=['POST'])
def download_automation_script():
    """Generate and return automation script for download"""
    try:
        data = request.get_json()
        script_content = data.get('script', '')
        filename = data.get('filename', 'catalyze_protocol.py')
        
        if not script_content:
            return jsonify({'error': 'Script content is required'}), 400
        
        return jsonify({
            'script': script_content,
            'filename': filename,
            'mime_type': 'text/python'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating script: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors for React routing"""
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create react-build directory if it doesn't exist
    if not os.path.exists('react-build'):
        os.makedirs('react-build')
    
    app.run(
        host='0.0.0.0',
        port=5003,
        debug=True
    )
