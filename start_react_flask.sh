#!/bin/bash

echo "🚀 Starting Catalyze React + Flask Application"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "flask_app.py" ]; then
    echo "❌ Error: flask_app.py not found. Please run this script from the Catalyze directory."
    exit 1
fi

# Create react-build directory if it doesn't exist
mkdir -p react-build

# Create a simple index.html for now (will be replaced by React build)
if [ ! -f "react-build/index.html" ]; then
    cat > react-build/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catalyze - AI Chemistry Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2563eb; text-align: center; margin-bottom: 30px; }
        .status { text-align: center; padding: 20px; background: #f0f9ff; border-radius: 8px; margin: 20px 0; }
        .api-status { color: #059669; font-weight: bold; }
        .instructions { background: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .code { background: #1f2937; color: #f9fafb; padding: 15px; border-radius: 5px; font-family: monospace; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Catalyze - AI Chemistry Assistant</h1>
        
        <div class="status">
            <h2>Flask Backend Running</h2>
            <p class="api-status">✅ API is active and ready</p>
            <p>Backend URL: <strong>http://localhost:5000</strong></p>
        </div>
        
        <div class="instructions">
            <h3>🚀 To start the React frontend:</h3>
            <ol>
                <li>Install Node.js dependencies: <div class="code">npm install</div></li>
                <li>Start React development server: <div class="code">npm start</div></li>
                <li>Open your browser to: <strong>http://localhost:3000</strong></li>
            </ol>
        </div>
        
        <div class="instructions">
            <h3>📱 For Hackathon Demo:</h3>
            <p>This Flask backend provides a professional API for your chemistry queries. The React frontend will provide a modern, mobile-friendly interface.</p>
            <p><strong>API Endpoints:</strong></p>
            <ul>
                <li><code>POST /api/query</code> - Process chemistry queries</li>
                <li><code>GET /api/history</code> - Get conversation history</li>
                <li><code>GET /api/demo-queries</code> - Get demo queries</li>
                <li><code>GET /api/health</code> - Health check</li>
            </ul>
        </div>
    </div>
</body>
</html>
EOF
fi

echo "✅ Flask backend starting on http://localhost:5000"
echo "📱 React frontend will be available on http://localhost:3000 (after npm start)"
echo ""
echo "🔧 To start React frontend in another terminal:"
echo "   npm install"
echo "   npm start"
echo ""
echo "🌐 For hackathon demo, share: http://localhost:3000"
echo ""

# Start Flask backend
python3 flask_app.py
