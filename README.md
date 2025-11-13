# 🧪 Catalyze - AI-Powered Chemistry Assistant

A beautiful, fully-functional AI chemistry assistant for material science and chemistry research.

## ✨ Features

- **🔬 Research Mode**: Ask chemistry questions and get detailed explanations
- **📋 Protocol Generation**: Generate step-by-step lab protocols
- **🤖 Lab Automation**: Create Python scripts for Opentrons, PyHamilton
- **🛡️ Safety Analysis**: Get safety information and hazard warnings
- **📊 Data Visualization**: Advanced charts and graphs with offline capability
- **🧮 Calculators**: Molarity, pH, reaction yield calculators
- **📝 Notes**: Take and save research notes
- **📤 Export**: Export protocols and data in multiple formats
- **🌙 Dark Mode**: Beautiful dark/light theme toggle
- **💜 Purple Gradient Theme**: Scientist-friendly UI design

## 🚀 Quick Start

### Option 1: Simple Start
```bash
./start_catalyze.sh
```

### Option 2: Manual Start
```bash
# Activate virtual environment
source venv/bin/activate

# Start the app
python app/flask_app.py
```

Then open: **http://localhost:5003**

### Option 3: With ChEMBL MCP Server (Advanced)
```bash
# Initialize submodules (first time only)
./manage_submodules.sh init

# Install Node.js dependencies
./manage_submodules.sh install

# Start the app
source venv/bin/activate && python app/flask_app.py
```

## 📁 Project Structure

```
mit-catalyze/
├── app/
│   └── flask_app.py        # Main Flask backend
├── react-build/
│   └── index.html          # Beautiful frontend (HTML/CSS/JS)
├── mcp_servers/
│   └── chembl-mcp-server/  # ChEMBL MCP Server (Git submodule)
├── src/
│   ├── clients/            # API clients (LLM, PubChem)
│   ├── generators/          # Protocol & automation generators
│   ├── config/             # Configuration files
│   └── pipeline.py          # Main processing pipeline
├── venv/                   # Python virtual environment
├── pyproject.toml          # Python dependencies
├── start_catalyze.sh       # Simple startup script
├── manage_submodules.sh     # Submodule management script
├── .gitmodules             # Git submodule configuration
└── README.md               # This file
```

## 🎯 What Makes This Special

- **Single HTML File**: Everything runs from one beautiful `react-build/index.html`
- **No React Build Process**: Pure HTML/CSS/JavaScript - fast and simple
- **Fully Functional**: All features work perfectly without internet
- **Beautiful UI**: Purple gradient theme with smooth animations
- **Clean Codebase**: Minimal, focused, and maintainable
- **🧪 ChEMBL Integration**: Access to 27 specialized chemistry tools via MCP
- **🤖 Hybrid AI**: Combines OpenAI knowledge with ChEMBL database accuracy

## 🧪 ChEMBL MCP Server Integration

This project integrates with the [ChEMBL MCP Server](https://github.com/Augmented-Nature/ChEMBL-MCP-Server) to provide access to 27 specialized chemistry tools:

### Core Features
- **Compound Search**: Search ChEMBL database by name, synonym, or identifier
- **Target Analysis**: Search biological targets and get detailed information
- **Bioactivity Data**: Access bioactivity measurements and assay results
- **Drug Development**: Search approved drugs and clinical candidates
- **Chemical Properties**: Analyze ADMET properties and drug-likeness

### How It Works
1. **Smart Routing**: Chemistry questions automatically trigger ChEMBL integration
2. **Hybrid Approach**: OpenAI provides main answers, ChEMBL enhances with database data
3. **Graceful Fallback**: If ChEMBL fails, you still get OpenAI responses
4. **Detailed Logging**: Track system behavior with comprehensive logs

### Submodule Management
```bash
# Check submodule status
./manage_submodules.sh status

# Update to latest version
./manage_submodules.sh update

# Reinstall dependencies
./manage_submodules.sh install
```

## 🔧 Dependencies

- **Python**: All dependencies in `pyproject.toml` and installed in `venv/`
- **Node.js**: Required for ChEMBL MCP Server (installed via submodule)

## 🌐 Access

- **Local**: http://localhost:5003
- **Network**: http://[your-ip]:5003

## 📱 Features Overview

1. **Chat Interface**: Ask chemistry questions with Research/Protocol/Automate/Safety modes
2. **Chat History**: Create named chats, manage conversation history
3. **Capabilities Display**: See what Catalyze can do
4. **Results Tabs**: Calculator, Notes, Data Visualizer, Export
5. **Dark Mode**: Toggle between light and dark themes
6. **Responsive Design**: Works on desktop and mobile

---

**Built for MIT Hackathon 2025** 🎓