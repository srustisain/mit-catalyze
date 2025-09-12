#!/usr/bin/env python3
"""
Simple Opentrons Protocol Generation Test
Based on the provided criteria for working Opentrons protocols
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.clients.opentrons_validator import OpentronsValidator, OpentronsCodeGenerator

# Test criteria from the user
TEST_CRITERIA = {
    "protocols": [
        {
            "name": "Simple Transfer",
            "description": "Pick up a tip, transfer 100µL of water from reservoir A1 to plate B1, then drop the tip.",
            "expected_elements": ["pick_up_tip", "aspirate", "dispense", "drop_tip", "reservoir", "plate"]
        },
        {
            "name": "Row Fill",
            "description": "Fill an entire row (row A) of the plate with 50µL from reservoir A1.",
            "expected_elements": ["rows", "transfer", "for loop", "reservoir", "plate"]
        },
        {
            "name": "Serial Dilution",
            "description": "Perform a 1:2 serial dilution across row A using 100µL transfers.",
            "expected_elements": ["serial dilution", "mix_after", "transfer", "for loop"]
        },
        {
            "name": "Multi-Dispense",
            "description": "Aspirate 200µL from reservoir A1 and dispense 50µL into 4 wells of row B.",
            "expected_elements": ["aspirate", "dispense", "multi-dispense", "for loop"]
        },
        {
            "name": "Mixing",
            "description": "Mix 5 times in plate well C1 with 150µL.",
            "expected_elements": ["mix", "pick_up_tip", "drop_tip"]
        }
    ]
}

def pretty_print_python_code(code: str, title: str = "Generated Code"):
    """Pretty print Python code with syntax highlighting"""
    print(f"\n{'='*80}")
    print(f"🐍 {title}")
    print('='*80)
    
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        print(f"{i:3d} | {line}")
    print('='*80)

async def test_protocol_generation():
    """Test Opentrons protocol generation against criteria"""
    print("🚀 Starting Simple Opentrons Protocol Generation Test...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize validator and generator
    validator = OpentronsValidator(max_retries=3)
    generator = OpentronsCodeGenerator(validator)
    
    results = []
    
    for i, protocol_criteria in enumerate(TEST_CRITERIA["protocols"], 1):
        print(f"\n🧪 Test {i}: {protocol_criteria['name']}")
        print(f"📝 Description: {protocol_criteria['description']}")
        
        try:
            # Generate protocol
            result = await generator.generate_with_validation(
                instructions=protocol_criteria['description'],
                context={},
                max_retries=2
            )
            
            if result['success']:
                print("✅ Generation: SUCCESS")
                
                # Pretty print the generated code
                pretty_print_python_code(result['code'], f"{protocol_criteria['name']} - Generated Code")
                
                # Validate the code
                validation_result = await validator.validate_code(result['code'])
                
                if validation_result.success:
                    print("✅ Validation: SUCCESS")
                    print(f"⏱️  Simulation Time: {validation_result.simulation_time:.3f}s")
                    
                    # Check for expected elements
                    code_lower = result['code'].lower()
                    found_elements = []
                    missing_elements = []
                    
                    for element in protocol_criteria['expected_elements']:
                        if element in code_lower:
                            found_elements.append(element)
                        else:
                            missing_elements.append(element)
                    
                    print(f"🔍 Expected Elements Found: {len(found_elements)}/{len(protocol_criteria['expected_elements'])}")
                    if found_elements:
                        print(f"   ✅ Found: {', '.join(found_elements)}")
                    if missing_elements:
                        print(f"   ❌ Missing: {', '.join(missing_elements)}")
                    
                    # Overall assessment
                    if len(found_elements) >= len(protocol_criteria['expected_elements']) * 0.7:  # 70% threshold
                        print("🎉 Overall: EXCELLENT")
                        test_result = "EXCELLENT"
                    elif len(found_elements) >= len(protocol_criteria['expected_elements']) * 0.5:  # 50% threshold
                        print("👍 Overall: GOOD")
                        test_result = "GOOD"
                    else:
                        print("⚠️  Overall: NEEDS IMPROVEMENT")
                        test_result = "NEEDS_IMPROVEMENT"
                        
                else:
                    print("❌ Validation: FAILED")
                    print(f"🚨 Errors: {len(validation_result.errors)}")
                    for error in validation_result.errors:
                        print(f"   - {error}")
                    test_result = "VALIDATION_FAILED"
                    
            else:
                print("❌ Generation: FAILED")
                print(f"🚨 Error: {result.get('error', 'Unknown error')}")
                test_result = "GENERATION_FAILED"
                
        except Exception as e:
            print(f"💥 Exception: {e}")
            test_result = "EXCEPTION"
        
        results.append({
            "name": protocol_criteria['name'],
            "result": test_result,
            "success": test_result in ["EXCELLENT", "GOOD"]
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print('='*80)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = (successful_tests / total_tests) * 100
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests} ✅")
    print(f"Failed: {total_tests - successful_tests} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for result in results:
        status_emoji = "✅" if result['success'] else "❌"
        print(f"  {status_emoji} {result['name']}: {result['result']}")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_protocol_generation())
