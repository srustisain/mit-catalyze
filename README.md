# 🧪 Catalyze - AI-Powered Chemistry Assistant

**Catalyze** is an AI-powered chemistry assistant that transforms research questions into detailed laboratory protocols and automation scripts. Built for the LLM Hackathon for Applications in Material Science & Chemistry.

## 🚀 Features

- **🔬 Research Questions**: Answer chemistry and materials science questions using PubChem data
- **📋 Protocol Generation**: Convert queries into step-by-step laboratory procedures
- **🤖 Lab Automation**: Generate Opentrons automation scripts for liquid handling
- **⚠️ Safety Information**: Get hazard warnings and safety precautions
- **📱 Mobile-Friendly**: Works on any device through web interface

## 🛠️ Tech Stack

- **Frontend**: Streamlit (mobile-responsive)
- **Backend**: Python FastAPI
- **LLM**: OpenAI GPT-3.5-turbo
- **Data Sources**: PubChem API
- **Automation**: Opentrons Python API

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Catalyze
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

5. **Access the app**:
   Open your browser and go to `http://localhost:8501`

## 🎯 Demo Queries

Try these example queries to see Catalyze in action:

- "Synthesize benzyl alcohol from benzyl chloride"
- "Which solid electrolytes are stable above 60°C?"
- "Top perovskites with band gap 1.3-1.7 eV"
- "Greener solvent replacements for DMF"

## 📱 Mobile Usage

Catalyze is designed to work on any device:
- **Smartphones**: Full functionality through web browser
- **Tablets**: Optimized interface for touch interaction
- **Desktop**: Full feature set with keyboard shortcuts

## 🔧 API Integration

### PubChem Integration
- Automatic chemical name extraction from queries
- Real-time chemical property lookup
- Safety information and hazard identification

### LLM Integration
- Protocol generation using OpenAI GPT-3.5-turbo
- "Explain Like I'm New" mode for educational content
- Safety validation and protocol optimization

### Opentrons Integration
- Automatic script generation for liquid handling
- Support for common labware and pipettes
- Protocol validation and optimization

## 📊 Example Output

### Protocol Generation
```
Step 1: Preparation
- Set up 50 mL round-bottom flask with magnetic stirrer
- Ensure proper ventilation

Step 2: Reaction Setup
- Dissolve benzyl chloride in 10 mL ethanol
- Add aqueous NaOH solution slowly with stirring

Step 3: Reaction
- Heat at 60°C for 3 hours under reflux
- Monitor reaction progress
```

### Automation Script
```python
from opentrons import protocol_api

def run(protocol: protocol_api.ProtocolContext):
    # Labware setup
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 2)
    pipette = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack])
    
    # Protocol steps
    pipette.transfer(100, plate['A1'], plate['B1'])
    pipette.mix(3, 150, plate['B1'])
```

## 🚨 Safety Features

- **Hazard Identification**: Automatic detection of toxic, corrosive, and flammable chemicals
- **Safety Precautions**: PPE recommendations and handling guidelines
- **Waste Management**: Proper disposal instructions for different waste streams
- **Protocol Validation**: Safety checks and completeness validation

## 🔮 Future Enhancements

- **PDF Upload**: Extract protocols from research papers
- **Reaction Visualization**: Interactive reaction diagrams
- **Green Chemistry Scoring**: Environmental impact assessment
- **Multi-language Support**: International accessibility
- **Advanced Automation**: Support for more lab equipment

## 🤝 Contributing

This project was built for the LLM Hackathon for Applications in Material Science & Chemistry. Contributions are welcome!

## 📄 License

This project is open source and available under the MIT License.

## 👥 Team

- **Samanvya Tripathi** - Backend Development & LLM Integration
- **Srusti Sain** - Frontend Development & UI/UX Design

## 🏆 Hackathon Submission

**Project Name**: Catalyze / ChemPilot / Alkemy  
**Category**: LLM Applications in Material Science & Chemistry  
**Demo**: [Live Demo Link]  
**Pitch**: [2-minute pitch video]

---

*Built with ❤️ for the chemistry and materials science community*


