#!/bin/bash

echo "🚀 Starting Catalyze - AI Chemistry Assistant"
echo "=============================================="

# Activate virtual environment
source venv/bin/activate

# Start Flask app
echo "✅ Starting Flask backend on http://localhost:5003"
python flask_app.py
