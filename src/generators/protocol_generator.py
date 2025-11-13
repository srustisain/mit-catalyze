from typing import Dict, List, Optional, Any
import re
from src.clients.llm_client import LLMClient

# Try to import Langfuse decorator
try:
    from langfuse.decorators import observe
except ImportError:
    # Create a no-op decorator if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

class ProtocolGenerator:
    """Generates and manages chemical protocols"""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    @observe()
    def generate_protocol(self, query: str, chemical_data: Dict[str, Any], explain_mode: bool = False) -> Dict[str, Any]:
        """Generate a protocol from query and chemical data"""
        return self.llm_client.generate_protocol(query, chemical_data, explain_mode)
    
    def get_safety_info(self, chemical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract safety information from chemical data"""
        safety_info = {
            'hazards': [],
            'precautions': [],
            'waste_info': ''
        }
        
        # Collect hazards from all chemicals
        all_hazards = set()
        for chemical, data in chemical_data.items():
            hazards = data.get('hazards', [])
            all_hazards.update(hazards)
        
        safety_info['hazards'] = list(all_hazards)
        
        # Generate precautions based on hazards
        precautions = []
        if any('toxic' in hazard.lower() for hazard in all_hazards):
            precautions.append("Use fume hood and appropriate PPE")
        if any('corrosive' in hazard.lower() for hazard in all_hazards):
            precautions.append("Wear acid-resistant gloves and eye protection")
        if any('flammable' in hazard.lower() for hazard in all_hazards):
            precautions.append("Keep away from open flames and heat sources")
        if any('irritant' in hazard.lower() for hazard in all_hazards):
            precautions.append("Avoid skin and eye contact")
        
        safety_info['precautions'] = precautions
        
        # Generate waste information
        waste_info = self._generate_waste_info(chemical_data)
        safety_info['waste_info'] = waste_info
        
        return safety_info
    
    def _generate_waste_info(self, chemical_data: Dict[str, Any]) -> str:
        """Generate waste management information"""
        waste_streams = []
        
        for chemical, data in chemical_data.items():
            formula = data.get('formula', '')
            if 'Cl' in formula or 'Br' in formula or 'I' in formula:
                waste_streams.append(f"{chemical}: Halogenated organic waste")
            elif 'S' in formula:
                waste_streams.append(f"{chemical}: Sulfur-containing waste")
            elif 'N' in formula:
                waste_streams.append(f"{chemical}: Nitrogen-containing waste")
            else:
                waste_streams.append(f"{chemical}: General organic waste")
        
        if waste_streams:
            return "Waste streams: " + "; ".join(waste_streams)
        else:
            return "Dispose of all waste according to local regulations"
    
    def validate_protocol(self, protocol: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a protocol for completeness"""
        validation = {
            'valid': True,
            'warnings': [],
            'suggestions': []
        }
        
        # Check for required fields
        if not protocol.get('steps'):
            validation['valid'] = False
            validation['warnings'].append("No protocol steps found")
        
        if not protocol.get('reaction'):
            validation['warnings'].append("No reaction equation provided")
        
        if not protocol.get('expected_yield'):
            validation['warnings'].append("No expected yield specified")
        
        # Check steps for completeness
        steps = protocol.get('steps', [])
        for i, step in enumerate(steps):
            if not step.get('description'):
                validation['warnings'].append(f"Step {i+1} missing description")
            if not step.get('reagents'):
                validation['warnings'].append(f"Step {i+1} missing reagent information")
            if not step.get('conditions'):
                validation['warnings'].append(f"Step {i+1} missing reaction conditions")
        
        # Add suggestions
        if len(steps) < 3:
            validation['suggestions'].append("Consider adding more detailed steps")
        
        if not protocol.get('safety_notes'):
            validation['suggestions'].append("Add safety considerations")
        
        return validation
    
    def format_protocol_for_export(self, protocol: Dict[str, Any]) -> str:
        """Format protocol for export as text"""
        output = []
        
        # Title
        output.append(f"# {protocol.get('title', 'Protocol')}")
        output.append("")
        
        # Reaction
        if protocol.get('reaction'):
            output.append(f"**Reaction:** {protocol['reaction']}")
            output.append("")
        
        # Steps
        output.append("## Procedure")
        steps = protocol.get('steps', [])
        for i, step in enumerate(steps, 1):
            output.append(f"### Step {i}: {step.get('title', 'Procedure Step')}")
            output.append(step.get('description', ''))
            
            if step.get('reagents'):
                output.append(f"**Reagents:** {step['reagents']}")
            
            if step.get('conditions'):
                output.append(f"**Conditions:** {step['conditions']}")
            
            if step.get('time'):
                output.append(f"**Time:** {step['time']}")
            
            output.append("")
        
        # Expected yield
        if protocol.get('expected_yield'):
            output.append(f"**Expected Yield:** {protocol['expected_yield']}")
            output.append("")
        
        # Safety notes
        if protocol.get('safety_notes'):
            output.append("## Safety Notes")
            output.append(protocol['safety_notes'])
            output.append("")
        
        # Explanation
        if protocol.get('explanation'):
            output.append("## Chemical Explanation")
            output.append(protocol['explanation'])
        
        return "\n".join(output)
    
    def get_protocol_summary(self, protocol: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the protocol"""
        steps = protocol.get('steps', [])
        
        summary = {
            'title': protocol.get('title', 'Protocol'),
            'total_steps': len(steps),
            'estimated_time': self._estimate_total_time(steps),
            'complexity': self._assess_complexity(steps),
            'safety_level': self._assess_safety_level(protocol),
            'expected_yield': protocol.get('expected_yield', 'Not specified')
        }
        
        return summary
    
    def _estimate_total_time(self, steps: List[Dict[str, Any]]) -> str:
        """Estimate total protocol time"""
        total_minutes = 0
        
        for step in steps:
            time_str = step.get('time', '')
            if 'hour' in time_str.lower():
                # Extract hours
                hours = re.findall(r'(\d+)\s*hour', time_str.lower())
                if hours:
                    total_minutes += int(hours[0]) * 60
            elif 'minute' in time_str.lower():
                # Extract minutes
                minutes = re.findall(r'(\d+)\s*minute', time_str.lower())
                if minutes:
                    total_minutes += int(minutes[0])
        
        if total_minutes == 0:
            return "Time not specified"
        elif total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes == 0:
                return f"{hours} hours"
            else:
                return f"{hours} hours {minutes} minutes"
    
    def _assess_complexity(self, steps: List[Dict[str, Any]]) -> str:
        """Assess protocol complexity"""
        if len(steps) <= 3:
            return "Simple"
        elif len(steps) <= 6:
            return "Moderate"
        else:
            return "Complex"
    
    def _assess_safety_level(self, protocol: Dict[str, Any]) -> str:
        """Assess safety level of the protocol"""
        safety_notes = protocol.get('safety_notes', '').lower()
        
        if any(word in safety_notes for word in ['toxic', 'corrosive', 'flammable', 'explosive']):
            return "High"
        elif any(word in safety_notes for word in ['irritant', 'hazardous', 'caution']):
            return "Medium"
        else:
            return "Low"
    
    def explain_like_new(self, query: str, chemical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple explanations for chemistry concepts"""
        try:
            # Extract key chemicals from the query
            chemicals = list(chemical_data.keys())
            
            # Generate explanation using LLM
            explanation_prompt = f"""
            Explain this chemistry concept in simple terms that a beginner can understand:
            Query: {query}
            Chemicals involved: {', '.join(chemicals)}
            
            Provide:
            1. A simple explanation of what's happening
            2. The type of reaction (if applicable)
            3. Why this reaction works
            4. A simple analogy or comparison
            5. Key safety points
            
            Keep it conversational and avoid jargon.
            """
            
            explanation = self.llm_client.generate_response(explanation_prompt)
            
            return {
                'simple_explanation': explanation,
                'reaction_type': self._identify_reaction_type(query),
                'analogy': self._generate_analogy(query),
                'safety_highlights': self._extract_safety_highlights(chemical_data)
            }
            
        except Exception as e:
            return {
                'simple_explanation': f"Error generating explanation: {str(e)}",
                'reaction_type': 'Unknown',
                'analogy': 'Unable to generate analogy',
                'safety_highlights': []
            }
    
    def get_relevant_papers(self, query: str) -> List[Dict[str, Any]]:
        """Get relevant literature papers (mock data for now)"""
        # In production, this would integrate with PubMed/arXiv APIs
        mock_papers = [
            {
                'title': 'Synthesis of Benzyl Alcohol from Benzyl Chloride: A Green Chemistry Approach',
                'authors': 'Smith, J.A., Johnson, B.C.',
                'journal': 'Journal of Organic Chemistry',
                'year': 2023,
                'doi': '10.1021/acs.joc.3c01234',
                'abstract': 'A novel method for the synthesis of benzyl alcohol from benzyl chloride using aqueous sodium hydroxide...',
                'relevance_score': 0.95,
                'url': 'https://pubs.acs.org/doi/10.1021/acs.joc.3c01234'
            },
            {
                'title': 'SN2 Substitution Reactions in Aqueous Media: Mechanistic Studies',
                'authors': 'Brown, M.D., Wilson, K.L.',
                'journal': 'Organic Letters',
                'year': 2022,
                'doi': '10.1021/acs.orglett.2c01567',
                'abstract': 'Comprehensive mechanistic studies of SN2 substitution reactions in aqueous environments...',
                'relevance_score': 0.87,
                'url': 'https://pubs.acs.org/doi/10.1021/acs.orglett.2c01567'
            },
            {
                'title': 'Green Solvents for Organic Synthesis: Recent Advances',
                'authors': 'Garcia, R., Lee, S.H.',
                'journal': 'Green Chemistry',
                'year': 2023,
                'doi': '10.1039/D3GC01234A',
                'abstract': 'Review of recent advances in green solvent systems for organic synthesis...',
                'relevance_score': 0.78,
                'url': 'https://pubs.rsc.org/en/content/articlelanding/2023/GC/D3GC01234A'
            }
        ]
        
        # Filter papers based on query relevance
        relevant_papers = []
        query_lower = query.lower()
        
        for paper in mock_papers:
            if any(term in query_lower for term in ['benzyl', 'alcohol', 'chloride', 'synthesis', 'sn2']):
                relevant_papers.append(paper)
        
        return relevant_papers[:5]  # Return top 5 most relevant
    
    def generate_knowledge_graph(self, chemical_data: Dict[str, Any], protocol: Dict[str, Any]) -> Dict[str, Any]:
        """Generate knowledge graph data for chemicals and reactions"""
        nodes = []
        edges = []
        
        # Add chemical nodes
        for chemical, data in chemical_data.items():
            nodes.append({
                'id': chemical,
                'label': chemical,
                'type': 'chemical',
                'properties': {
                    'molecular_weight': data.get('molecular_weight', 'Unknown'),
                    'formula': data.get('formula', 'Unknown'),
                    'hazards': data.get('hazards', [])
                }
            })
        
        # Add reaction node
        if protocol.get('reaction'):
            nodes.append({
                'id': 'reaction',
                'label': 'Reaction',
                'type': 'reaction',
                'properties': {
                    'equation': protocol['reaction'],
                    'yield': protocol.get('expected_yield', 'Unknown')
                }
            })
            
            # Add edges from reactants to reaction
            for chemical in chemical_data.keys():
                edges.append({
                    'from': chemical,
                    'to': 'reaction',
                    'type': 'reactant'
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'layout': 'force'  # For D3.js force layout
        }
    
    def export_to_markdown(self, protocol: Dict[str, Any]) -> str:
        """Export protocol to Markdown format"""
        return self.format_protocol_for_export(protocol)
    
    def _identify_reaction_type(self, query: str) -> str:
        """Identify the type of reaction from the query"""
        query_lower = query.lower()
        
        if 'sn2' in query_lower or 'substitution' in query_lower:
            return 'SN2 Substitution'
        elif 'oxidation' in query_lower:
            return 'Oxidation'
        elif 'reduction' in query_lower:
            return 'Reduction'
        elif 'addition' in query_lower:
            return 'Addition'
        elif 'elimination' in query_lower:
            return 'Elimination'
        else:
            return 'Organic Synthesis'
    
    def _generate_analogy(self, query: str) -> str:
        """Generate a simple analogy for the reaction"""
        query_lower = query.lower()
        
        if 'sn2' in query_lower or 'substitution' in query_lower:
            return "Like musical chairs - one group (Cl⁻) leaves and another group (OH⁻) takes its place"
        elif 'oxidation' in query_lower:
            return "Like rusting - the molecule gains oxygen or loses electrons"
        elif 'reduction' in query_lower:
            return "Like cleaning - the molecule loses oxygen or gains electrons"
        else:
            return "Like cooking - mixing ingredients to create something new"
    
    def _extract_safety_highlights(self, chemical_data: Dict[str, Any]) -> List[str]:
        """Extract key safety highlights from chemical data"""
        highlights = []
        
        for chemical, data in chemical_data.items():
            hazards = data.get('hazards', [])
            for hazard in hazards:
                if 'toxic' in hazard.lower():
                    highlights.append(f"{chemical} is toxic - use fume hood")
                elif 'corrosive' in hazard.lower():
                    highlights.append(f"{chemical} is corrosive - wear protective gear")
                elif 'flammable' in hazard.lower():
                    highlights.append(f"{chemical} is flammable - keep away from heat")
        
        return highlights[:3]  # Return top 3 safety highlights
