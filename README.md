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

[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange?style=flat&logo=openai&logoColor=white)](https://openai.com)
[![ChEMBL](https://img.shields.io/badge/ChEMBL-Database-red?style=flat&logo=databricks&logoColor=white)](https://www.ebi.ac.uk/chembl/)
[![MIT](https://img.shields.io/badge/MIT-Hackathon%202025-yellow?style=flat&logo=mit&logoColor=white)](https://hackathon.mit.edu)

---

## 🌟 **What is Catalyze?**

Catalyze is a cutting-edge AI chemistry assistant that combines the power of specialized AI agents with comprehensive chemical databases to provide intelligent, context-aware assistance for chemistry research, protocol generation, lab automation, and safety analysis. Built with a sophisticated agent-based architecture, Catalyze offers multi-platform automation support, PDF analysis capabilities, and seamless integration with ChEMBL's extensive chemical database.

### 🎯 **Key Highlights**

- **🤖 Multi-Agent Architecture**: 5 specialized AI agents for different chemistry tasks
- **🔬 Dual Platform Automation**: Generate both OpenTrons Python and Lynx C# scripts
- **📄 PDF Analysis**: Upload and analyze scientific papers with AI
- **🧪 ChEMBL Integration**: Access to 27 specialized chemistry tools and databases
- **🛡️ Safety-First Design**: Comprehensive safety analysis and hazard assessment
- **🎨 Beautiful UI**: Modern, responsive interface with dark/light themes
- **⚡ Real-time Processing**: Fast, intelligent responses with context awareness

---

## ✨ **Core Features**

### 🔬 **Research Agent**
- **Chemical Properties**: Detailed analysis of molecular structures, properties, and behaviors
- **Database Integration**: Access to ChEMBL, PubChem, and other chemical databases
- **Literature Search**: Find and analyze relevant research papers and studies
- **Compound Analysis**: Comprehensive compound information and structure analysis
- **Target Research**: Biological target analysis and pathway information

### 📋 **Protocol Agent**
- **Step-by-Step Protocols**: Generate detailed, reproducible laboratory procedures
- **Safety Integration**: Built-in safety considerations and hazard warnings
- **Material Lists**: Automatic generation of required materials and equipment
- **Method Optimization**: Suggestions for improving experimental efficiency
- **Documentation**: Professional protocol formatting with clear instructions

### 🤖 **Automation Agent**
- **Multi-Platform Support**: Generate code for both OpenTrons OT2 and Dynamic Device Lynx
- **Platform Selection**: Interactive platform choice for automation scripts
- **Python Scripts**: OpenTrons OT2 automation with full API integration
- **C# Scripts**: Dynamic Device Lynx automation with comprehensive liquid handling
- **Code Validation**: Built-in validation and error checking for generated scripts

### 🛡️ **Safety Agent**
- **Hazard Assessment**: Comprehensive safety analysis of chemicals and procedures
- **Risk Evaluation**: Detailed risk assessment with mitigation strategies
- **Safety Protocols**: Generate safety procedures and emergency protocols
- **Chemical Safety**: MSDS integration and safety data analysis
- **Compliance**: Ensure adherence to safety standards and regulations

### 📄 **PDF Analysis**
- **Document Upload**: Drag-and-drop PDF upload with progress tracking
- **AI Analysis**: OpenAI GPT-4o powered document analysis and summarization
- **Context Integration**: PDF content automatically integrated into chat responses
- **Multi-Format Support**: Support for scientific papers, protocols, and reports
- **Smart Extraction**: Intelligent extraction of key information and methodologies

---

## 🏗️ **Architecture Overview**

### **Agent-Based System**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Router Agent  │────│ Pipeline Manager│────│  Specialized    │
│  (Query Router) │    │   (Orchestrator)│    │     Agents      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼───┐ ┌─────▼─────┐ ┌───▼─────┐
            │ Research  │ │ Protocol  │ │Automate │
            │   Agent   │ │   Agent   │ │  Agent  │
            └───────────┘ └───────────┘ └─────────┘
                    │           │           │
            ┌───────▼───┐ ┌─────▼─────┐
            │  Safety   │ │   MCP     │
            │   Agent   │ │  Tools    │
            └───────────┘ └───────────┘
```

### **Technology Stack**
- **Backend**: Python 3.12+, Flask 3.1+, LangChain, LangGraph
- **AI Integration**: OpenAI GPT-4o, ChEMBL MCP Server
- **Frontend**: Pure HTML/CSS/JavaScript (no build process required)
- **Automation**: OpenTrons API, Dynamic Device Lynx C# integration
- **PDF Processing**: PyMuPDF, OpenAI Vision API
- **Database**: ChEMBL, PubChem integration via MCP

---

## 🚀 **Quick Start Guide**

### **Prerequisites**
- Python 3.12 or higher
- Node.js (for ChEMBL MCP Server)
- OpenAI API key
- Git

### **Option 1: Simple Start (Recommended)**
```bash
./start_catalyze.sh
```

### **Option 2: Manual Setup**
```bash
# Activate virtual environment
source venv/bin/activate

# Start the app
python app/flask_app.py
```

Then open: **http://localhost:5003**

### **Option 3: Advanced Setup with ChEMBL**
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

---

## 🛠️ **Development**

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### **Development Setup**
```bash
# Clone and setup
git clone https://github.com/your-username/mit-catalyze.git
cd mit-catalyze

# Create development environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run in development mode
python app/flask_app.py --debug
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