#!/usr/bin/env python3
"""
Test script to verify markdown rendering functionality
"""

def test_markdown_examples():
    """Test various markdown examples"""
    
    # Test 1: Basic markdown with code
    basic_markdown = """# Opentrons Protocol

This is a **simple** Opentrons protocol for liquid transfer.

## Code Example

Here's the Python code:

```python
from opentrons import protocol_api

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
```

## Features

- ✅ **Validated** with Opentrons simulation
- ✅ **Ready to use** in production
- ✅ **Well documented** with comments

> **Note**: This protocol has been tested and validated.
"""
    
    # Test 2: Multiple code blocks
    multi_code = """# Multiple Code Examples

## Python Code
```python
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
```

## JavaScript Code
```javascript
function greet(name) {
    return `Hello, ${name}!`;
}
```

## HTML Code
```html
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>
```
"""
    
    # Test 3: Lists and formatting
    lists_markdown = """# Protocol Steps

## Materials Needed

1. **Pipette tips** (300µL)
2. **96-well plate** (source)
3. **96-well plate** (destination)
4. **Liquid samples**

## Procedure

### Step 1: Setup
- Load tip rack in position 1
- Load source plate in position 2
- Load destination plate in position 3

### Step 2: Transfer
- Pick up tip
- Aspirate 100µL from source
- Dispense 100µL to destination
- Drop tip

### Step 3: Cleanup
- Dispose of used tips
- Clean work area
- Document results

## Safety Notes

> ⚠️ **Important**: Always wear appropriate PPE when handling chemicals.

- Use proper ventilation
- Follow lab safety protocols
- Dispose of waste properly
"""
    
    return {
        "basic": basic_markdown,
        "multi_code": multi_code,
        "lists": lists_markdown
    }

if __name__ == "__main__":
    print("🧪 Testing markdown examples...")
    
    examples = test_markdown_examples()
    
    print("\n📝 Basic Markdown Example:")
    print("```markdown")
    print(examples["basic"])
    print("```")
    
    print("\n🔧 Multi-Code Example:")
    print("```markdown")
    print(examples["multi_code"])
    print("```")
    
    print("\n📋 Lists Example:")
    print("```markdown")
    print(examples["lists"])
    print("```")
    
    print("\n✅ Markdown examples generated!")
