import sys 
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
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

@app.route('/api/chat', methods=['POST'])
def chat_with_llm():
    """Chat with LLM using OpenAI + ChEMBL MCP Server"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Check if this is a chemistry-related question that should use MCP
        chemistry_keywords = [
            'molecular weight', 'compound', 'chemical', 'drug', 'molecule',
            'aspirin', 'caffeine', 'ibuprofen', 'target', 'receptor',
            'bioactivity', 'admet', 'solubility', 'pharmacology',
            'synthesis', 'reaction', 'mechanism', 'pathway'
        ]
        
        message_lower = message.lower()
        is_chemistry_question = any(keyword in message_lower for keyword in chemistry_keywords)
        
        if is_chemistry_question:
            # Use hybrid approach: OpenAI + ChEMBL MCP
            print(f"🧪 Chemistry question detected: {message}")
            
            # First, get OpenAI response
            from src.clients.llm_client import LLMClient
            llm_client = LLMClient(provider="openai")
            openai_response = llm_client.generate_chat_response(message, conversation_history)
            print(f"✅ OpenAI response generated: {len(openai_response)} characters")
            
            # Then try to enhance with ChEMBL data
            chembl_enhancement = ""
            try:
                from src.pipeline import run_pipeline
                print("🔍 Attempting ChEMBL MCP integration...")
                
                # Run the MCP pipeline
                result = run_pipeline(message, explain_mode=True)
                print(f"📊 MCP result keys: {list(result.keys())}")
                
                # Extract ChEMBL data
                enhancement_parts = []
                
                if result.get('chemicals') and len(result['chemicals']) > 0:
                    chemicals = result['chemicals']
                    enhancement_parts.append(f"ChEMBL Database: Found {len(chemicals)} chemicals: {', '.join(chemicals)}")
                    print(f"🧪 Found chemicals: {chemicals}")
                
                if result.get('chemical_data'):
                    for chem, data in result['chemical_data'].items():
                        if data.get('molecular_weight'):
                            enhancement_parts.append(f"ChEMBL Data: {chem} molecular weight = {data['molecular_weight']} g/mol")
                            print(f"⚖️  {chem} MW: {data['molecular_weight']} g/mol")
                        if data.get('formula'):
                            enhancement_parts.append(f"ChEMBL Data: {chem} formula = {data['formula']}")
                            print(f"🧬 {chem} formula: {data['formula']}")
                
                if result.get('protocol') and result['protocol']:
                    protocol = result['protocol']
                    if protocol.get('title'):
                        enhancement_parts.append(f"ChEMBL Protocol: {protocol['title']}")
                        print(f"📋 Protocol: {protocol['title']}")
                
                if enhancement_parts:
                    chembl_enhancement = "\n\n**Additional ChEMBL Database Information:**\n" + "\n".join(enhancement_parts)
                    print(f"✅ ChEMBL enhancement added: {len(chembl_enhancement)} characters")
                else:
                    print("⚠️  No ChEMBL data extracted")
                
            except Exception as mcp_error:
                print(f"❌ MCP pipeline error: {mcp_error}")
                chembl_enhancement = "\n\n(Note: ChEMBL database access temporarily unavailable)"
            
            # Combine OpenAI response with ChEMBL enhancement
            response = openai_response + chembl_enhancement
            print(f"🎯 Final response length: {len(response)} characters")
        else:
            # Use basic LLM for non-chemistry questions
            from src.clients.llm_client import LLMClient
            llm_client = LLMClient(provider="openai")
            response = llm_client.generate_chat_response(message, conversation_history)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'used_mcp': is_chemistry_question
        })

    except Exception as e:
        return jsonify({'error': f'Error processing chat: {str(e)}'}), 500

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
