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
python flask_app.py
```

Then open: **http://localhost:5003**

## 📁 Project Structure

```
mit-catalyze/
├── flask_app.py              # Main Flask backend
├── react-build/
│   └── index.html           # Beautiful frontend (HTML/CSS/JS)
├── venv/                    # Python virtual environment
├── requirements.txt         # Python dependencies
├── start_catalyze.sh       # Simple startup script
├── README.md               # This file
└── Python modules:
    ├── pubchem_client.py   # PubChem API integration
    ├── llm_client.py       # LLM integration
    ├── protocol_generator.py # Protocol generation
    └── automation_generator.py # Lab automation scripts
```

## 🎯 What Makes This Special

- **Single HTML File**: Everything runs from one beautiful `react-build/index.html`
- **No React Build Process**: Pure HTML/CSS/JavaScript - fast and simple
- **Fully Functional**: All features work perfectly without internet
- **Beautiful UI**: Purple gradient theme with smooth animations
- **Clean Codebase**: Minimal, focused, and maintainable

## 🔧 Dependencies

All Python dependencies are in `requirements.txt` and installed in the `venv/` folder.

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