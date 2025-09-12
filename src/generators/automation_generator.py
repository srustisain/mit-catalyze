from typing import Dict, List, Optional, Any
import re

class AutomationGenerator:
    """Generates Opentrons automation scripts from protocols"""
    
    def __init__(self):
        self.tip_racks = ['opentrons_96_tiprack_300ul', 'opentrons_96_tiprack_1000ul']
        self.plates = ['corning_96_wellplate_360ul_flat', 'corning_384_wellplate_112ul_flat']
        self.pipettes = ['p300_single', 'p1000_single']
    
    def generate_script(self, protocol: Dict[str, Any], chemical_data: Dict[str, Any]) -> str:
        """Generate Opentrons script from protocol"""
        
        # Extract liquid handling steps from protocol
        liquid_steps = self._extract_liquid_steps(protocol)
        
        if not liquid_steps:
            return self._generate_basic_script(protocol, chemical_data)
        
        # Generate full automation script
        script = self._generate_full_script(liquid_steps, chemical_data)
        
        return script
    
    def _extract_liquid_steps(self, protocol: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract liquid handling steps from protocol"""
        liquid_steps = []
        
        steps = protocol.get('steps', [])
        for step in steps:
            description = step.get('description', '').lower()
            reagents = step.get('reagents', '').lower()
            
            # Look for liquid handling keywords
            if any(keyword in description for keyword in ['add', 'transfer', 'pipette', 'dispense', 'mix']):
                # Extract volumes and chemicals
                volumes = self._extract_volumes(description + ' ' + reagents)
                chemicals = self._extract_chemicals_from_step(step)
                
                if volumes and chemicals:
                    liquid_steps.append({
                        'step': step,
                        'volumes': volumes,
                        'chemicals': chemicals,
                        'action': self._determine_action(description)
                    })
        
        return liquid_steps
    
    def _extract_volumes(self, text: str) -> List[float]:
        """Extract volumes from text"""
        volumes = []
        
        # Common volume patterns
        patterns = [
            r'(\d+(?:\.\d+)?)\s*ml',
            r'(\d+(?:\.\d+)?)\s*mL',
            r'(\d+(?:\.\d+)?)\s*μl',
            r'(\d+(?:\.\d+)?)\s*μL',
            r'(\d+(?:\.\d+)?)\s*ul',
            r'(\d+(?:\.\d+)?)\s*UL'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                volume = float(match)
                # Convert to microliters for Opentrons
                if 'ml' in pattern.lower():
                    volume *= 1000
                volumes.append(volume)
        
        return volumes
    
    def _extract_chemicals_from_step(self, step: Dict[str, Any]) -> List[str]:
        """Extract chemical names from a protocol step"""
        chemicals = []
        
        reagents = step.get('reagents', '')
        description = step.get('description', '')
        
        # Common chemical patterns
        chemical_patterns = [
            r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:chloride|bromide|iodide|fluoride|oxide|hydroxide|sulfate|nitrate|acetate|alcohol|acid|amine|ether|ester|ketone|aldehyde)\b',
            r'\b(?:benzyl|methyl|ethyl|propyl|butyl|phenyl|tolyl|naphthyl)\s+\w+\b',
            r'\b(?:sodium|potassium|calcium|magnesium|aluminum|iron|copper|zinc)\s+\w+\b',
            r'\b(?:NaOH|KOH|HCl|H2SO4|HNO3|NaCl|KCl|CaCl2|MgCl2)\b',
            r'\b(?:DMF|DMSO|THF|EtOH|MeOH|AcOH|TFA|DCM|CHCl3|CCl4)\b'
        ]
        
        text = reagents + ' ' + description
        
        for pattern in chemical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            chemicals.extend(matches)
        
        return list(set(chemicals))  # Remove duplicates
    
    def _determine_action(self, description: str) -> str:
        """Determine the type of liquid handling action"""
        description = description.lower()
        
        if 'mix' in description or 'stir' in description:
            return 'mix'
        elif 'add' in description or 'transfer' in description:
            return 'transfer'
        elif 'dispense' in description:
            return 'dispense'
        else:
            return 'transfer'
    
    def _generate_basic_script(self, protocol: Dict[str, Any], chemical_data: Dict[str, Any]) -> str:
        """Generate a basic Opentrons script when no liquid steps are found"""
        
        script = '''from opentrons import protocol_api

metadata = {
    'apiLevel': '2.11',
    'protocolName': 'Generated Protocol',
    'author': 'Catalyze AI',
    'description': 'Automatically generated protocol from Catalyze'
}

def run(protocol: protocol_api.ProtocolContext):
    # Labware setup
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 2)
    pipette = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack])
    
    # Protocol steps
    protocol.comment("Starting generated protocol...")
    
    # Add your protocol steps here
    # This is a template - specific steps depend on your protocol
    
    protocol.comment("Protocol completed!")
'''
        
        return script
    
    def _generate_full_script(self, liquid_steps: List[Dict[str, Any]], chemical_data: Dict[str, Any]) -> str:
        """Generate a full Opentrons script with liquid handling steps"""
        
        script_parts = [
            "from opentrons import protocol_api",
            "",
            "metadata = {",
            "    'apiLevel': '2.11',",
            "    'protocolName': 'Generated Protocol',",
            "    'author': 'Catalyze AI',",
            "    'description': 'Automatically generated protocol from Catalyze'",
            "}",
            "",
            "def run(protocol: protocol_api.ProtocolContext):",
            "    # Labware setup",
            "    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 1)",
            "    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 2)",
            "    pipette = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack])",
            "",
            "    # Protocol steps",
            "    protocol.comment('Starting generated protocol...')",
            ""
        ]
        
        # Add liquid handling steps
        for i, step_data in enumerate(liquid_steps):
            step = step_data['step']
            volumes = step_data['volumes']
            chemicals = step_data['chemicals']
            action = step_data['action']
            
            script_parts.append(f"    # Step {i+1}: {step.get('title', 'Liquid Handling')}")
            script_parts.append(f"    protocol.comment('{step.get('description', '')}')")
            
            if action == 'transfer' and volumes and chemicals:
                # Generate transfer commands
                for j, (volume, chemical) in enumerate(zip(volumes, chemicals)):
                    if j < len(volumes):
                        source_well = f"A{j+1}"
                        dest_well = f"B{j+1}"
                        
                        script_parts.append(f"    # Transfer {volume} μL of {chemical}")
                        script_parts.append(f"    pipette.pick_up_tip()")
                        script_parts.append(f"    pipette.transfer({volume}, plate['{source_well}'], plate['{dest_well}'], new_tip='never')")
                        script_parts.append(f"    pipette.drop_tip()")
                        script_parts.append("")
            
            elif action == 'mix' and volumes:
                # Generate mixing commands
                script_parts.append(f"    # Mixing step")
                script_parts.append(f"    pipette.pick_up_tip()")
                script_parts.append(f"    pipette.mix(3, {volumes[0]}, plate['B1'])")
                script_parts.append(f"    pipette.drop_tip()")
                script_parts.append("")
        
        # Add incubation and other steps
        script_parts.extend([
            "    # Incubation steps (manual)",
            "    protocol.comment('Incubate as specified in protocol - manual step')",
            "",
            "    # Final steps",
            "    protocol.comment('Protocol completed!')"
        ])
        
        return "\n".join(script_parts)
    
    def generate_script_for_synthesis(self, query: str, chemical_data: Dict[str, Any]) -> str:
        """Generate a specific script for synthesis reactions"""
        
        if "benzyl alcohol" in query.lower() and "benzyl chloride" in query.lower():
            return self._generate_benzyl_alcohol_script(chemical_data)
        
        return self._generate_basic_script({}, chemical_data)
    
    def _generate_benzyl_alcohol_script(self, chemical_data: Dict[str, Any]) -> str:
        """Generate specific script for benzyl alcohol synthesis"""
        
        script = '''from opentrons import protocol_api

metadata = {
    'apiLevel': '2.11',
    'protocolName': 'Benzyl Alcohol Synthesis',
    'author': 'Catalyze AI',
    'description': 'Synthesis of benzyl alcohol from benzyl chloride'
}

def run(protocol: protocol_api.ProtocolContext):
    # Labware setup
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 2)
    pipette = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack])
    
    # Protocol steps
    protocol.comment('Starting benzyl alcohol synthesis...')
    
    # Step 1: Transfer benzyl chloride (simulate 100 μL)
    protocol.comment('Step 1: Adding benzyl chloride')
    pipette.pick_up_tip()
    pipette.transfer(100, plate['A1'], plate['B1'], new_tip='never')
    pipette.drop_tip()
    
    # Step 2: Add ethanol (simulate 200 μL)
    protocol.comment('Step 2: Adding ethanol')
    pipette.pick_up_tip()
    pipette.transfer(200, plate['A2'], plate['B1'], new_tip='never')
    pipette.drop_tip()
    
    # Step 3: Add NaOH solution (simulate 50 μL)
    protocol.comment('Step 3: Adding NaOH solution')
    pipette.pick_up_tip()
    pipette.transfer(50, plate['A3'], plate['B1'], new_tip='never')
    pipette.drop_tip()
    
    # Step 4: Mix the reaction mixture
    protocol.comment('Step 4: Mixing reaction mixture')
    pipette.pick_up_tip()
    pipette.mix(5, 150, plate['B1'])
    pipette.drop_tip()
    
    # Step 5: Incubation (manual step)
    protocol.comment('Step 5: Incubate at 60°C for 3 hours (manual step)')
    
    # Step 6: Add extraction solvent (simulate 100 μL)
    protocol.comment('Step 6: Adding extraction solvent')
    pipette.pick_up_tip()
    pipette.transfer(100, plate['A4'], plate['B1'], new_tip='never')
    pipette.drop_tip()
    
    # Step 7: Final mixing
    protocol.comment('Step 7: Final mixing')
    pipette.pick_up_tip()
    pipette.mix(3, 100, plate['B1'])
    pipette.drop_tip()
    
    protocol.comment('Synthesis protocol completed!')
    protocol.comment('Note: Heating, extraction, and purification steps require manual intervention.')
'''
        
        return script
    
    def validate_script(self, script: str) -> Dict[str, Any]:
        """Validate the generated Opentrons script"""
        validation = {
            'valid': True,
            'warnings': [],
            'suggestions': []
        }
        
        # Check for required components
        if 'protocol_api' not in script:
            validation['valid'] = False
            validation['warnings'].append("Missing protocol_api import")
        
        if 'def run(' not in script:
            validation['valid'] = False
            validation['warnings'].append("Missing run function")
        
        if 'load_labware' not in script:
            validation['warnings'].append("No labware loaded")
        
        if 'load_instrument' not in script:
            validation['warnings'].append("No pipette loaded")
        
        # Check for common issues
        if 'pick_up_tip()' in script and 'drop_tip()' not in script:
            validation['warnings'].append("Tips picked up but not dropped")
        
        if 'transfer(' in script and 'new_tip=' not in script:
            validation['suggestions'].append("Consider specifying new_tip parameter for transfers")
        
        return validation
    
    def get_script_summary(self, script: str) -> Dict[str, Any]:
        """Get a summary of the generated script"""
        summary = {
            'total_transfers': script.count('transfer('),
            'total_mixes': script.count('mix('),
            'has_incubation': 'incubate' in script.lower(),
            'has_heating': 'heat' in script.lower() or '60°c' in script.lower(),
            'estimated_duration': self._estimate_script_duration(script)
        }
        
        return summary
    
    def _estimate_script_duration(self, script: str) -> str:
        """Estimate the duration of the script"""
        transfers = script.count('transfer(')
        mixes = script.count('mix(')
        
        # Rough estimation: 30 seconds per transfer, 20 seconds per mix
        total_seconds = (transfers * 30) + (mixes * 20)
        
        if total_seconds < 60:
            return f"{total_seconds} seconds"
        else:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if seconds == 0:
                return f"{minutes} minutes"
            else:
                return f"{minutes} minutes {seconds} seconds"
