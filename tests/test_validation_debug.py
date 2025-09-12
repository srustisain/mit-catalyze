#!/usr/bin/env python3
import asyncio
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.opentrons_validator import OpentronsValidator

async def test_validation():
    print("🧪 Testing Opentrons validation with different code types...")
    
    validator = OpentronsValidator()
    
    # Test 1: Generic text (like what the UI shows)
    print("\n1. Testing generic text:")
    generic_text = """To write code for Opentrons, you will typically use the Opentrons API (Application Programming Interface) in Python. Here are the general steps to write code for an Opentrons robot:

1. Set up your development environment: Make sure you have Python installed on your computer. You will also need to install the Opentrons API. You can find detailed instructions on how to set up your environment on the Opentrons website.

2. Write your protocol: Start by importing the necessary modules from the Opentrons API. You will typically import the labware, instruments, and protocol modules. Define your labware (pipettes, tip racks, etc.) and instruments (pipettes, modules) that you will be using in your protocol.

3. Define your protocol steps: Write the code to specify the actions you want the robot to perform. This can include actions like picking up tips, transferring liquids, moving the pipette to different locations, etc.

4. Run your protocol: Once you have written your protocol, you can run it on an Opentrons robot. You can either run your protocol using the Opentrons App or run it through the Opentrons API using the command line.

Here is a simple example of a protocol written using the Opentrons API:

python
from opentrons import labware, instruments, robot

Define labware
tiprack = labware.load('opentrons-tiprack-300ul', '1')
plate = labware.load('96-flat', '2')

Define pipette
pipette = instruments.P300Single(mount='right', tipracks=[tiprack])

Run protocol
def run(protocol):
pipette.pickuptip()
pipette.aspirate(100, plate['A1'])
pipette.dispense(100, plate['B1'])
pipette.droptip()

This is just a simple example to get you started. You can find more information and examples in the Opentrons API documentation. Make sure to familiarize yourself with the API and the capabilities of the Opentrons robot before writing your protocols."""
    
    result1 = await validator.validate_code(generic_text)
    print(f"   Success: {result1.success}")
    print(f"   Errors: {result1.errors}")
    print(f"   Warnings: {result1.warnings}")
    
    # Test 2: Actual Opentrons code
    print("\n2. Testing actual Opentrons code:")
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
    
    result2 = await validator.validate_code(opentrons_code)
    print(f"   Success: {result2.success}")
    print(f"   Errors: {result2.errors}")
    print(f"   Warnings: {result2.warnings}")
    
    # Test 3: Invalid Python code
    print("\n3. Testing invalid Python code:")
    invalid_code = "print('hello world'"
    
    result3 = await validator.validate_code(invalid_code)
    print(f"   Success: {result3.success}")
    print(f"   Errors: {result3.errors}")
    print(f"   Warnings: {result3.warnings}")

if __name__ == "__main__":
    asyncio.run(test_validation())
