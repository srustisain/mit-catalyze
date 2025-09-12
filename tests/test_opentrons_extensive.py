#!/usr/bin/env python3
"""
Extensive test script for Opentrons code generation and validation
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.automate_agent import AutomateAgent
from src.clients.opentrons_validator import OpentronsValidator, OpentronsCodeGenerator

class OpentronsTestSuite:
    """Comprehensive test suite for Opentrons integration"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test results with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"[{timestamp}] {status} {test_name}")
        if details:
            print(f"         {details}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": timestamp,
            "data": data
        })
    
    def print_code_block(self, code: str, title: str = "Generated Code"):
        """Pretty print Python code with syntax highlighting"""
        print(f"\n{'='*80}")
        print(f"🐍 {title}")
        print(f"{'='*80}")
        
        # Add line numbers and basic syntax highlighting
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # Basic syntax highlighting
            if line.strip().startswith('#'):
                print(f"{i:3d} | \033[32m{line}\033[0m")  # Green for comments
            elif line.strip().startswith(('def ', 'class ', 'from ', 'import ')):
                print(f"{i:3d} | \033[34m{line}\033[0m")  # Blue for keywords
            elif line.strip().startswith(('    ', '\t')):
                print(f"{i:3d} | \033[36m{line}\033[0m")  # Cyan for indented code
            elif '=' in line and not line.strip().startswith('#'):
                print(f"{i:3d} | \033[33m{line}\033[0m")  # Yellow for assignments
            else:
                print(f"{i:3d} | {line}")
        
        print(f"{'='*80}\n")
    
    def print_validation_result(self, result, title: str = "Validation Result"):
        """Pretty print validation results"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
        
        print(f"Status: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
        print(f"Simulation Time: {result.simulation_time:.3f}s" if result.simulation_time else "N/A")
        
        if result.errors:
            print(f"\n🚨 Errors ({len(result.errors)}):")
            for i, error in enumerate(result.errors, 1):
                print(f"  {i}. {error}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for i, warning in enumerate(result.warnings, 1):
                print(f"  {i}. {warning}")
        
        if result.suggestions:
            print(f"\n💡 Suggestions ({len(result.suggestions)}):")
            for i, suggestion in enumerate(result.suggestions, 1):
                print(f"  {i}. {suggestion}")
        
        print(f"{'='*60}\n")
    
    async def test_basic_initialization(self):
        """Test basic component initialization"""
        print("\n🚀 Testing Basic Initialization...")
        
        # Test OpentronsValidator
        try:
            validator = OpentronsValidator(max_retries=3)
            self.log_test("OpentronsValidator Init", True, "Initialized with 3 max retries")
        except Exception as e:
            self.log_test("OpentronsValidator Init", False, f"Failed: {e}")
            return False
        
        # Test AutomateAgent
        try:
            agent = AutomateAgent()
            self.log_test("AutomateAgent Init", True, "Initialized successfully")
        except Exception as e:
            self.log_test("AutomateAgent Init", False, f"Failed: {e}")
            return False
        
        # Test OpentronsCodeGenerator
        try:
            generator = OpentronsCodeGenerator(validator)
            self.log_test("OpentronsCodeGenerator Init", True, "Initialized with validator")
        except Exception as e:
            self.log_test("OpentronsCodeGenerator Init", False, f"Failed: {e}")
            return False
        
        return True
    
    async def test_opentrons_detection(self):
        """Test Opentrons request detection"""
        print("\n🔍 Testing Opentrons Request Detection...")
        
        agent = AutomateAgent()
        
        test_cases = [
            ("Create an Opentrons protocol for PCR setup", True),
            ("Generate OT-2 liquid handling script", True),
            ("Make a Flex protocol for sample preparation", True),
            ("Create a PyHamilton automation script", False),
            ("Generate a general lab automation script", False),
            ("Transfer 100μL from A1 to B1 using pipette", True),
            ("Set up a thermocycler protocol", True),
            ("Create a simple Python script", False),
        ]
        
        for query, expected in test_cases:
            result = agent._is_opentrons_request(query)
            success = result == expected
            self.log_test(
                f"Detection: '{query[:30]}...'", 
                success, 
                f"Expected: {expected}, Got: {result}"
            )
    
    async def test_code_validation_success(self):
        """Test validation with valid Opentrons code"""
        print("\n✅ Testing Code Validation - Success Cases...")
        
        validator = OpentronsValidator()
        
        valid_codes = [
            {
                "name": "Basic Protocol",
                "code": '''
from opentrons import protocol_api

metadata = {
    'protocolName': 'Basic Transfer Protocol',
    'author': 'Test Suite',
    'description': 'Simple liquid transfer protocol',
    'apiLevel': '2.13'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tip_rack])
    
    # Transfer 100μL from A1 to B1
    pipette.pick_up_tip()
    pipette.aspirate(100, plate['A1'])
    pipette.dispense(100, plate['B1'])
    pipette.drop_tip()
'''
            },
            {
                "name": "Multi-Well Transfer",
                "code": '''
from opentrons import protocol_api

metadata = {
    'protocolName': 'Multi-Well Transfer',
    'author': 'Test Suite',
    'description': 'Transfer from multiple wells',
    'apiLevel': '2.13'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    source_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    dest_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '3')
    
    # Load pipette
    pipette = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tip_rack])
    
    # Transfer from column 1 to column 2
    pipette.pick_up_tip()
    pipette.transfer(100, source_plate.columns()[0], dest_plate.columns()[1], new_tip='never')
    pipette.drop_tip()
'''
            }
        ]
        
        for test_case in valid_codes:
            print(f"\n🧪 Testing: {test_case['name']}")
            self.print_code_block(test_case['code'], f"{test_case['name']} - Input")
            
            try:
                result = await validator.validate_code(test_case['code'])
                self.print_validation_result(result, f"{test_case['name']} - Validation")
                
                success = result.success
                self.log_test(
                    f"Validation: {test_case['name']}", 
                    success,
                    f"Success: {success}, Time: {result.simulation_time:.3f}s"
                )
                
            except Exception as e:
                self.log_test(f"Validation: {test_case['name']}", False, f"Exception: {e}")
    
    async def test_code_validation_errors(self):
        """Test validation with intentionally problematic code"""
        print("\n❌ Testing Code Validation - Error Cases...")
        
        validator = OpentronsValidator()
        
        error_cases = [
            {
                "name": "Syntax Error",
                "code": '''
from opentrons import protocol_api

metadata = {
    'protocolName': 'Bad Syntax Protocol',
    'author': 'Test Suite',
    'description': 'Protocol with syntax errors',
    'apiLevel': '2.13'
}

def run(protocol: protocol_api.ProtocolContext):
    # This will cause a syntax error
    undefined_variable = some_undefined_function()
    pass
'''
            },
            {
                "name": "Import Error",
                "code": '''
from opentrons import protocol_api
import nonexistent_module

metadata = {
    'protocolName': 'Import Error Protocol',
    'author': 'Test Suite',
    'description': 'Protocol with import errors',
    'apiLevel': '2.13'
}

def run(protocol: protocol_api.ProtocolContext):
    pass
'''
            },
            {
                "name": "Missing Metadata",
                "code": '''
from opentrons import protocol_api

def run(protocol: protocol_api.ProtocolContext):
    pass
'''
            }
        ]
        
        for test_case in error_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            self.print_code_block(test_case['code'], f"{test_case['name']} - Input")
            
            try:
                result = await validator.validate_code(test_case['code'])
                self.print_validation_result(result, f"{test_case['name']} - Validation")
                
                # For error cases, we expect validation to fail
                expected_failure = not result.success
                self.log_test(
                    f"Error Validation: {test_case['name']}", 
                    expected_failure,
                    f"Expected failure: {expected_failure}, Errors: {len(result.errors)}"
                )
                
            except Exception as e:
                self.log_test(f"Error Validation: {test_case['name']}", True, f"Exception caught: {e}")
    
    async def test_retry_mechanism(self):
        """Test the retry mechanism with failing code"""
        print("\n🔄 Testing Retry Mechanism...")
        
        generator = OpentronsCodeGenerator()
        
        # Test with instructions that will likely cause issues
        problematic_instructions = [
            "Create a protocol with syntax errors and undefined functions",
            "Generate code that will fail validation multiple times",
            "Make a protocol that uses invalid Opentrons API calls"
        ]
        
        for i, instructions in enumerate(problematic_instructions, 1):
            print(f"\n🧪 Retry Test {i}: {instructions}")
            
            try:
                start_time = time.time()
                result = await generator.generate_with_validation(
                    instructions=instructions,
                    context={},
                    max_retries=3
                )
                end_time = time.time()
                
                print(f"\n📊 Retry Results:")
                print(f"   Success: {result['success']}")
                print(f"   Attempts: {result['attempts']}")
                print(f"   Total Time: {end_time - start_time:.3f}s")
                
                if result['code']:
                    self.print_code_block(result['code'], f"Generated Code (Attempt {result['attempts']})")
                
                if result.get('validation_result'):
                    self.print_validation_result(
                        result['validation_result'], 
                        f"Final Validation Result"
                    )
                
                self.log_test(
                    f"Retry Test {i}", 
                    True, 
                    f"Attempts: {result['attempts']}, Success: {result['success']}"
                )
                
            except Exception as e:
                self.log_test(f"Retry Test {i}", False, f"Exception: {e}")
    
    async def test_automate_agent_workflow(self):
        """Test complete AutomateAgent workflow"""
        print("\n🤖 Testing AutomateAgent Complete Workflow...")
        
        agent = AutomateAgent()
        
        test_queries = [
            {
                "query": "Create an Opentrons protocol for transferring 100μL from A1 to B1",
                "expected_opentrons": True
            },
            {
                "query": "Generate a PyHamilton automation script for sample preparation",
                "expected_opentrons": False
            },
            {
                "query": "Make a Flex protocol for PCR setup with 96-well plate",
                "expected_opentrons": True
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case['query']
            expected_opentrons = test_case['expected_opentrons']
            
            print(f"\n🧪 Workflow Test {i}: {query}")
            
            try:
                # Test the complete workflow
                result = await agent.process_query(query, {})
                
                print(f"\n📊 Workflow Results:")
                print(f"   Success: {result['success']}")
                print(f"   Agent: {result.get('agent', 'Unknown')}")
                print(f"   Response Length: {len(result.get('response', ''))}")
                
                if result.get('opentrons_code'):
                    self.print_code_block(result['opentrons_code'], "Generated Opentrons Code")
                
                if result.get('validation_result'):
                    self.print_validation_result(result['validation_result'], "Validation Result")
                
                # Check if Opentrons detection worked as expected
                is_opentrons = agent._is_opentrons_request(query)
                detection_correct = is_opentrons == expected_opentrons
                
                self.log_test(
                    f"Workflow Test {i}", 
                    result['success'] and detection_correct,
                    f"Success: {result['success']}, Detection: {is_opentrons} (expected: {expected_opentrons})"
                )
                
            except Exception as e:
                self.log_test(f"Workflow Test {i}", False, f"Exception: {e}")
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n⚡ Testing Performance Benchmarks...")
        
        validator = OpentronsValidator()
        
        # Test with a complex protocol
        complex_protocol = '''
from opentrons import protocol_api

metadata = {
    'protocolName': 'Complex Multi-Step Protocol',
    'author': 'Performance Test',
    'description': 'Complex protocol for performance testing',
    'apiLevel': '2.13'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load multiple labware
    tip_rack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    tip_rack_1000 = protocol.load_labware('opentrons_96_tiprack_1000ul', '2')
    source_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '3')
    dest_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '4')
    temp_module = protocol.load_module('temperature module gen2', '5')
    temp_plate = temp_module.load_labware('corning_96_wellplate_360ul_flat')
    
    # Load pipettes
    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tip_rack_300])
    p1000 = protocol.load_instrument('p1000_single_gen2', 'left', tip_racks=[tip_rack_1000])
    
    # Complex protocol steps
    for i in range(8):  # 8 columns
        p300.pick_up_tip()
        for j in range(12):  # 12 rows
            source_well = source_plate.wells()[i*12 + j]
            dest_well = dest_plate.wells()[i*12 + j]
            p300.transfer(50, source_well, dest_well, new_tip='never')
        p300.drop_tip()
    
    # Temperature control
    temp_module.set_temperature(37)
    protocol.delay(minutes=5)
    temp_module.deactivate()
'''
        
        print("🧪 Testing Complex Protocol Performance...")
        self.print_code_block(complex_protocol, "Complex Protocol - Input")
        
        try:
            start_time = time.time()
            result = await validator.validate_code(complex_protocol)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            self.print_validation_result(result, "Complex Protocol - Validation")
            
            self.log_test(
                "Performance: Complex Protocol",
                result.success,
                f"Success: {result.success}, Time: {total_time:.3f}s, Simulation: {result.simulation_time:.3f}s"
            )
            
        except Exception as e:
            self.log_test("Performance: Complex Protocol", False, f"Exception: {e}")
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*80}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        print(f"\n{'='*80}")
        
        # Save results to file
        results_file = f"opentrons_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100,
                    'total_time': total_time
                },
                'test_results': self.test_results
            }, f, indent=2)
        
        print(f"📁 Detailed results saved to: {results_file}")
        print(f"{'='*80}\n")

async def main():
    """Main test runner"""
    print("🚀 Starting Extensive Opentrons Integration Tests...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_suite = OpentronsTestSuite()
    
    # Run all tests
    await test_suite.test_basic_initialization()
    await test_suite.test_opentrons_detection()
    await test_suite.test_code_validation_success()
    await test_suite.test_code_validation_errors()
    await test_suite.test_retry_mechanism()
    await test_suite.test_automate_agent_workflow()
    await test_suite.test_performance_benchmarks()
    
    # Print summary
    test_suite.print_test_summary()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
