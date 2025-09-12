#!/usr/bin/env python3
"""
Test script to verify syntax highlighting functionality
"""

def test_python_code():
    """Test Python code highlighting"""
    python_code = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

number = 5
result = factorial(number)
print(f"The factorial of {number} is {result}")
"""
    return python_code

def test_opentrons_code():
    """Test Opentrons code highlighting"""
    opentrons_code = """
from opentrons import protocol_api

metadata = {
    'protocolName': 'Simple Transfer',
    'author': 'Test',
    'description': 'A simple transfer protocol',
    'apiLevel': '2.13'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tip_rack])
    
    # Transfer liquid
    pipette.pick_up_tip()
    pipette.aspirate(100, plate['A1'])
    pipette.dispense(100, plate['B1'])
    pipette.drop_tip()
"""
    return opentrons_code

def test_html_code():
    """Test HTML code highlighting"""
    html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Block Example</title>
    <style>
        pre {
            background-color: #f4f4f4;
            border: 1px solid #ddd;
            padding: 10px;
            overflow-x: auto;
        }
        code {
            font-family: 'Courier New', Courier, monospace;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>Python Code Example</h1>
    <pre><code>
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
    </code></pre>
</body>
</html>
"""
    return html_code

if __name__ == "__main__":
    print("🧪 Testing syntax highlighting examples...")
    
    print("\n📝 Python Code:")
    print("```python")
    print(test_python_code().strip())
    print("```")
    
    print("\n🤖 Opentrons Code:")
    print("```python")
    print(test_opentrons_code().strip())
    print("```")
    
    print("\n🌐 HTML Code:")
    print("```html")
    print(test_html_code().strip())
    print("```")
    
    print("\n✅ Test examples generated!")
