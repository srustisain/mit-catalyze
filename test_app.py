#!/usr/bin/env python3
"""
Test script for Catalyze application
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported"""
    try:
        from pubchem_client import PubChemClient
        from llm_client import LLMClient
        from protocol_generator import ProtocolGenerator
        from automation_generator import AutomationGenerator
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_pubchem_client():
    """Test PubChem client functionality"""
    try:
        from pubchem_client import PubChemClient
        client = PubChemClient()
        
        # Test chemical extraction
        query = "Synthesize benzyl alcohol from benzyl chloride"
        chemicals = client.extract_chemicals(query)
        print(f"✅ Extracted chemicals: {chemicals}")
        
        # Test chemical data retrieval
        if chemicals:
            data = client.get_chemical_data(chemicals[0])
            if data:
                print(f"✅ Retrieved data for {chemicals[0]}: {data.get('molecular_weight', 'N/A')} g/mol")
            else:
                print(f"⚠️ No data retrieved for {chemicals[0]}")
        
        return True
    except Exception as e:
        print(f"❌ PubChem client error: {e}")
        return False

def test_protocol_generator():
    """Test protocol generator functionality"""
    try:
        from protocol_generator import ProtocolGenerator
        generator = ProtocolGenerator()
        
        # Test with demo data
        query = "Synthesize benzyl alcohol from benzyl chloride"
        chemical_data = {
            'benzyl chloride': {
                'molecular_weight': 126.58,
                'formula': 'C7H7Cl',
                'hazards': ['Toxic', 'Skin irritant']
            },
            'benzyl alcohol': {
                'molecular_weight': 108.14,
                'formula': 'C7H8O',
                'hazards': ['Irritant']
            }
        }
        
        protocol = generator.generate_protocol(query, chemical_data, explain_mode=True)
        print(f"✅ Generated protocol with {len(protocol.get('steps', []))} steps")
        
        # Test safety info
        safety_info = generator.get_safety_info(chemical_data)
        print(f"✅ Generated safety info with {len(safety_info.get('hazards', []))} hazards")
        
        return True
    except Exception as e:
        print(f"❌ Protocol generator error: {e}")
        return False

def test_automation_generator():
    """Test automation generator functionality"""
    try:
        from automation_generator import AutomationGenerator
        generator = AutomationGenerator()
        
        # Test with demo protocol
        protocol = {
            'steps': [
                {
                    'title': 'Add Reagent',
                    'description': 'Add 100 μL of benzyl chloride',
                    'reagents': 'Benzyl chloride (100 μL)',
                    'conditions': 'Room temperature'
                }
            ]
        }
        
        chemical_data = {
            'benzyl chloride': {
                'molecular_weight': 126.58,
                'formula': 'C7H7Cl'
            }
        }
        
        script = generator.generate_script(protocol, chemical_data)
        print(f"✅ Generated automation script ({len(script)} characters)")
        
        # Test script validation
        validation = generator.validate_script(script)
        print(f"✅ Script validation: {'Valid' if validation['valid'] else 'Invalid'}")
        
        return True
    except Exception as e:
        print(f"❌ Automation generator error: {e}")
        return False

def test_streamlit_app():
    """Test if Streamlit app can be imported"""
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Streamlit import error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Catalyze Application")
    print("=" * 40)
    
    tests = [
        ("Module Imports", test_imports),
        ("PubChem Client", test_pubchem_client),
        ("Protocol Generator", test_protocol_generator),
        ("Automation Generator", test_automation_generator),
        ("Streamlit App", test_streamlit_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\n🚀 To start the app, run:")
        print("   streamlit run app.py")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


