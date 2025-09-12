# 🧪 Catalyze - AI-Powered Chemistry Assistant

<div align="center">

![Catalyze Logo](https://img.shields.io/badge/Catalyze-AI%20Chemistry%20Assistant-purple?style=for-the-badge&logo=flask&logoColor=white)

**A sophisticated AI-powered chemistry assistant for material science and chemistry research, featuring specialized agents, multi-platform automation, and comprehensive chemical knowledge integration.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange?style=flat&logo=openai&logoColor=white)](https://openai.com)
[![ChEMBL](https://img.shields.io/badge/ChEMBL-Database-red?style=flat&logo=databricks&logoColor=white)](https://www.ebi.ac.uk/chembl/)
[![MIT](https://img.shields.io/badge/MIT-Hackathon%202025-yellow?style=flat&logo=mit&logoColor=white)](https://hackathon.mit.edu)

</div>

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

### **Installation Methods**

#### **Method 1: UV (Recommended)**
UV is a fast Python package manager that's significantly faster than pip:

```bash
# Install UV (if not already installed)
# On Windows:
pip install uv

# On macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup with UV
git clone https://github.com/your-username/mit-catalyze.git
cd mit-catalyze

# Install dependencies with UV (creates virtual environment automatically)
uv sync

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Set up environment variables
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Start the application
uv run python app/flask_app.py
```

#### **Method 2: Traditional pip**
```bash
# Clone and navigate
git clone https://github.com/your-username/mit-catalyze.git
cd mit-catalyze

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Set up environment variables
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Start the application
python app/flask_app.py
```

### **Option 1: Simple Start (Recommended)**
```bash
# Clone the repository
git clone https://github.com/your-username/mit-catalyze.git
cd mit-catalyze

# Run the startup script
./start_catalyze.sh
```

### **Option 3: Advanced Setup with ChEMBL**
```bash
# Initialize submodules (first time only)
./manage_submodules.sh init

# Install Node.js dependencies
./manage_submodules.sh install

# Start with full MCP integration
source .venv/bin/activate && python app/flask_app.py
```

### **Access the Application**
- **Local**: http://localhost:5003
- **Network**: http://[your-ip]:5003

---

## 📁 **Project Structure**

```
mit-catalyze/
├── 📁 app/
│   └── flask_app.py              # Main Flask backend application
├── 📁 react-build/
│   ├── index.html                # Beautiful frontend (single file)
│   └── static/                   # CSS, JS, and assets
├── 📁 mcp_servers/
│   ├── chembl-mcp-server/        # ChEMBL MCP Server (submodule)
│   └── opentrons-mcp-server/     # OpenTrons MCP Server (submodule)
├── 📁 src/
│   ├── 📁 agents/                # AI Agent implementations
│   │   ├── base_agent.py         # Base class for all agents
│   │   ├── router_agent.py       # Query routing and classification
│   │   ├── research_agent.py     # Chemistry research and analysis
│   │   ├── protocol_agent.py     # Lab protocol generation
│   │   ├── automate_agent.py     # Lab automation scripts
│   │   └── safety_agent.py       # Safety analysis and hazards
│   ├── 📁 api/
│   │   └── chat_endpoints.py     # REST API endpoints
│   ├── 📁 clients/
│   │   ├── llm_client.py         # OpenAI integration
│   │   ├── pubchem_client.py     # PubChem API client
│   │   └── opentrons_validator.py # OpenTrons code validation
│   ├── 📁 generators/
│   │   ├── protocol_generator.py # Protocol generation logic
│   │   ├── automation_generator.py # Automation script generation
│   │   └── lynx_generator.py     # Lynx C# script generation
│   ├── 📁 pipeline/
│   │   ├── pipeline_manager.py   # Main processing pipeline
│   │   └── mode_processor.py     # Mode-specific processing
│   ├── 📁 config/
│   │   ├── config.py             # Application configuration
│   │   └── logging_config.py     # Logging configuration
│   └── 📁 prompts/
│       ├── research_agent.txt    # Research agent prompts
│       ├── protocol_agent.txt    # Protocol agent prompts
│       ├── automate_agent.txt    # Automation agent prompts
│       └── safety_agent.txt      # Safety agent prompts
├── 📁 docs/
│   ├── AGENT_ARCHITECTURE_SUMMARY.md
│   ├── PDF_UPLOAD_FEATURE.md
│   ├── MCP_CONFIGURATION.md
│   └── SETUP.md
├── 📁 tests/
│   └── [comprehensive test suite]
├── pyproject.toml                # Python dependencies
├── start_catalyze.sh             # Quick start script
├── manage_submodules.sh          # Submodule management
└── README.md                     # This file
```

---

## 🧪 **Usage Examples**

### **Research Questions**
```
User: "What are the properties of caffeine?"
Agent: [Provides detailed molecular analysis, pharmacological effects, 
        safety data, and research findings from ChEMBL database]
```

### **Protocol Generation**
```
User: "Generate a protocol for synthesizing aspirin"
Agent: [Creates step-by-step procedure with materials list, 
        safety considerations, and detailed instructions]
```

### **Lab Automation**
```
User: "Generate code for serial dilution"
Agent: [Asks for platform selection: OpenTrons or Lynx]
User: "Lynx"
Agent: [Generates complete C# script for Dynamic Device Lynx system]
```

### **Safety Analysis**
```
User: "What are the safety hazards of working with sulfuric acid?"
Agent: [Provides comprehensive safety analysis, hazard warnings, 
        protective equipment requirements, and emergency procedures]
```

### **PDF Analysis**
```
User: [Uploads research paper PDF]
User: "What are the key findings in this paper?"
Agent: [Analyzes PDF content and provides detailed summary 
        of findings, methodology, and implications]
```

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional
DEBUG=true
LOG_LEVEL=INFO
MCP_SERVER_URL=http://localhost:8000
```

### **MCP Server Configuration**
```python
# config.py
MCP_SERVERS = {
    "chembl": {
        "transport": "streamable_http",
        "url": "http://localhost:8000/mcp"
    },
    "opentrons": {
        "transport": "stdio",
        "command": "node",
        "args": ["./mcp_servers/opentrons-mcp-server/dist/index.js"]
    }
}
```

---

## 🧪 **ChEMBL Integration**

Catalyze integrates with the [ChEMBL MCP Server](https://github.com/Augmented-Nature/ChEMBL-MCP-Server) to provide access to 27 specialized chemistry tools:

### **Available Tools**
- **Compound Search**: Search by name, synonym, or identifier
- **Target Analysis**: Biological target information and pathways
- **Bioactivity Data**: Assay results and activity measurements
- **Drug Development**: Approved drugs and clinical candidates
- **Chemical Properties**: ADMET properties and drug-likeness
- **Structure Search**: Similarity and substructure searches
- **Dose Response**: Pharmacological data analysis

### **Integration Benefits**
- **Hybrid AI**: Combines OpenAI knowledge with ChEMBL database accuracy
- **Real-time Data**: Access to up-to-date chemical information
- **Comprehensive Coverage**: 2+ million compounds and 1+ million assays
- **Professional Grade**: Industry-standard chemical database integration

---

## 🤖 **Automation Platforms**

### **OpenTrons OT2 (Python)**
```python
# Generated Python script example
from opentrons import protocol_api

metadata = {
    'protocolName': 'Serial Dilution Protocol',
    'author': 'Catalyze AI',
    'apiLevel': '2.13'
}

def run(protocol: protocol_api.ProtocolContext):
    # Complete automation script
    pass
```

### **Dynamic Device Lynx (C#)**
```csharp
// Generated C# script example
using System;
using MethodManager.Core;
using MMScriptObjects;

public class SerialDilutionProtocol : IMMScriptExecutor
{
    public void Execute(IMMApp app)
    {
        // Complete Lynx automation script
    }
}
```

---

## 📊 **API Endpoints**

### **Chat Processing**
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What are the properties of caffeine?",
  "mode": "research",
  "conversation_history": [],
  "pdf_context": null
}
```

### **PDF Upload**
```http
POST /api/upload-pdf
Content-Type: multipart/form-data

pdf: [PDF file]
```

### **Agent Information**
```http
GET /api/agents
```

### **Health Check**
```http
GET /api/health
```

---

## 🧪 **Testing**

### **Run Test Suite**
```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_agents.py
python -m pytest tests/test_automation.py
python -m pytest tests/test_pdf_upload.py
```

### **Test Coverage**
- **Agent System**: All 5 agents tested
- **API Endpoints**: Complete endpoint testing
- **PDF Processing**: Upload and analysis testing
- **Automation**: Both OpenTrons and Lynx code generation
- **MCP Integration**: ChEMBL server connectivity

---

## 🚀 **Performance & Scalability**

### **Performance Metrics**
- **Response Time**: < 2 seconds for most queries
- **Concurrent Users**: Supports multiple simultaneous users
- **Memory Usage**: Optimized for efficient resource utilization
- **Database Queries**: Cached responses for common queries

### **Scalability Features**
- **Agent-Based Architecture**: Easy to scale individual components
- **Async Processing**: Non-blocking operations for better performance
- **Caching**: Intelligent caching for improved response times
- **Modular Design**: Easy to add new agents and features

---

## 🔒 **Security & Privacy**

### **Data Protection**
- **Local Processing**: All data processed locally when possible
- **Secure API Keys**: Environment variable protection
- **Temporary Files**: Automatic cleanup of uploaded files
- **No Data Storage**: No persistent storage of user data

### **Safety Features**
- **Input Validation**: Comprehensive input sanitization
- **Error Handling**: Graceful error recovery
- **Rate Limiting**: Protection against abuse
- **Secure Headers**: CORS and security headers

---

## 🛠️ **Development**

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### **Development Setup**

#### **With UV (Recommended)**
```bash
# Clone and setup
git clone https://github.com/your-username/mit-catalyze.git
cd mit-catalyze

# Install with UV (includes dev dependencies)
uv sync --dev

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run in development mode
uv run python app/flask_app.py --debug
```

#### **With pip**
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

### **Code Style**
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use modern ES6+ syntax
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: Maintain high test coverage

---

## 📈 **Roadmap**

### **Upcoming Features**
- **Multi-PDF Support**: Analyze multiple documents simultaneously
- **Advanced Visualization**: Interactive molecular structure viewers
- **Collaboration**: Real-time collaborative protocol editing
- **Mobile App**: Native mobile application
- **API Expansion**: Public API for third-party integrations

### **Technical Improvements**
- **Database Integration**: Persistent storage for user data
- **Caching Layer**: Redis-based caching for improved performance
- **Microservices**: Containerized microservices architecture
- **CI/CD**: Automated testing and deployment pipeline

---

## 🤝 **Contributing**

We welcome contributions from the chemistry and AI communities! Here's how you can help:

### **Ways to Contribute**
- **Bug Reports**: Report issues and bugs
- **Feature Requests**: Suggest new features
- **Code Contributions**: Submit pull requests
- **Documentation**: Improve documentation
- **Testing**: Help test new features

### **Getting Started**
1. Check the [Issues](https://github.com/your-username/mit-catalyze/issues) page
2. Read the [Contributing Guide](CONTRIBUTING.md)
3. Join our [Discord](https://discord.gg/catalyze) community
4. Start contributing!

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **MIT Hackathon 2025** for the inspiration and platform
- **OpenAI** for providing the GPT-4o API
- **ChEMBL** for the comprehensive chemical database
- **OpenTrons** for the automation platform integration
- **Dynamic Devices** for the Lynx system support
- **The Chemistry Community** for feedback and support

---

## 📞 **Support & Contact**

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/mit-catalyze/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/mit-catalyze/discussions)
- **Email**: catalyze-support@mit.edu

---

<div align="center">

**Built with ❤️ for the Chemistry Community**

![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red?style=for-the-badge)
![MIT Hackathon 2025](https://img.shields.io/badge/MIT%20Hackathon-2025-yellow?style=for-the-badge)

</div>