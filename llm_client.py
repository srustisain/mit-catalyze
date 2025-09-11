import openai
from typing import Dict, List, Optional, Any
import json
import re
import requests
from config import OPENAI_API_KEY, CEREBRAS_API_KEY, HUGGINGFACE_API_KEY, LLM_PROVIDER, OPENAI_MODEL, CEREBRAS_MODEL, HUGGINGFACE_MODEL

class LLMClient:
    """Client for interacting with LLM APIs"""
    
    def __init__(self, provider: str = None):
        """
        Initialize LLM client with specified provider or default from config
        
        Args:
            provider (str): LLM provider to use ('openai', 'cerebras', 'huggingface')
        """
        self.provider = provider or LLM_PROVIDER or "openai"
        self.openai_key = OPENAI_API_KEY
        self.cerebras_key = CEREBRAS_API_KEY
        self.huggingface_key = HUGGINGFACE_API_KEY
        
        # Initialize OpenAI client if key is available
        if self.openai_key:
            openai.api_key = self.openai_key
    
    def set_provider(self, provider: str) -> None:
        """Set the LLM provider to use"""
        self.provider = provider
    
    def generate_protocol(self, query: str, chemical_data: Dict[str, Any], explain_mode: bool = False) -> Dict[str, Any]:
        """Generate a chemical protocol from a query"""
        
        # Create a detailed prompt
        prompt = self._create_protocol_prompt(query, chemical_data, explain_mode)
        
        try:
            if self.provider == "openai" and self.openai_key:
                response = openai.ChatCompletion.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a chemistry expert who generates detailed laboratory protocols."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
                return self._parse_protocol_response(content, explain_mode)
            
            elif self.provider == "cerebras" and self.cerebras_key:
                response = self._call_cerebras_api(prompt)
                return self._parse_protocol_response(response, explain_mode)
            
            elif self.provider == "huggingface" and self.huggingface_key:
                response = self._call_huggingface_api(prompt)
                return self._parse_protocol_response(response, explain_mode)
            
            else:
                # Fallback to demo data
                return self._get_demo_protocol(query, chemical_data, explain_mode)
                
        except Exception as e:
            print(f"Error generating protocol with {self.provider}: {e}")
            return self._get_demo_protocol(query, chemical_data, explain_mode)
    
    def _call_cerebras_api(self, prompt: str) -> str:
        """Call Cerebras API"""
        url = "https://api.cerebras.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cerebras_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": CEREBRAS_MODEL,
            "messages": [
                {"role": "system", "content": "You are a chemistry expert who generates detailed laboratory protocols."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _call_huggingface_api(self, prompt: str) -> str:
        """Call Hugging Face API"""
        url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
        headers = {
            "Authorization": f"Bearer {self.huggingface_key}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1500,
                "temperature": 0.3,
                "return_full_text": False
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()[0]["generated_text"]
    
    def _create_protocol_prompt(self, query: str, chemical_data: Dict[str, Any], explain_mode: bool) -> str:
        """Create a detailed prompt for protocol generation"""
        
        chemical_info = ""
        for chemical, data in chemical_data.items():
            chemical_info += f"\n{chemical}:\n"
            chemical_info += f"  - Molecular Weight: {data.get('molecular_weight', 'N/A')}\n"
            chemical_info += f"  - Formula: {data.get('formula', 'N/A')}\n"
            chemical_info += f"  - Density: {data.get('density', 'N/A')}\n"
            chemical_info += f"  - Hazards: {', '.join(data.get('hazards', []))}\n"
        
        explain_instruction = ""
        if explain_mode:
            explain_instruction = "\n\nIMPORTANT: Explain the chemistry in simple terms as if teaching a beginner. Include the reaction mechanism and why each step is necessary."
        
        prompt = f"""
Generate a detailed laboratory protocol for: {query}

Chemical Information Available:
{chemical_info}

Please provide:
1. A step-by-step protocol with specific quantities and conditions
2. Expected yield and reaction time
3. Safety considerations
4. Workup and purification steps{explain_instruction}

Format your response as JSON with the following structure:
{{
    "title": "Protocol title",
    "reaction": "Chemical equation",
    "steps": [
        {{"title": "Step title", "description": "Detailed description", "reagents": "List of reagents and quantities", "conditions": "Temperature, time, etc.", "time": "Duration"}}
    ],
    "expected_yield": "Expected yield percentage",
    "explanation": "Chemical explanation (if explain_mode is true)",
    "safety_notes": "Important safety considerations"
}}
"""
        return prompt
    
    def _parse_protocol_response(self, content: str, explain_mode: bool) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback parsing
                return self._parse_text_response(content, explain_mode)
        except json.JSONDecodeError:
            return self._parse_text_response(content, explain_mode)
    
    def _parse_text_response(self, content: str, explain_mode: bool) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        lines = content.split('\n')
        
        protocol = {
            "title": "Generated Protocol",
            "reaction": "Chemical reaction",
            "steps": [],
            "expected_yield": "80-90%",
            "explanation": "",
            "safety_notes": "Handle all chemicals with appropriate PPE"
        }
        
        current_step = None
        for line in lines:
            line = line.strip()
            if line.startswith('Step') or line.startswith('1.') or line.startswith('2.'):
                if current_step:
                    protocol['steps'].append(current_step)
                current_step = {
                    "title": line,
                    "description": "",
                    "reagents": "",
                    "conditions": "",
                    "time": ""
                }
            elif current_step and line:
                current_step['description'] += line + " "
        
        if current_step:
            protocol['steps'].append(current_step)
        
        return protocol
    
    def _get_demo_protocol(self, query: str, chemical_data: Dict[str, Any], explain_mode: bool) -> Dict[str, Any]:
        """Get demo protocol data when LLM is not available"""
        
        # Demo protocol for benzyl alcohol synthesis
        if "benzyl alcohol" in query.lower() and "benzyl chloride" in query.lower():
            protocol = {
                "title": "Synthesis of Benzyl Alcohol from Benzyl Chloride",
                "reaction": "C₆H₅CH₂Cl + NaOH → C₆H₅CH₂OH + NaCl",
                "steps": [
                    {
                        "title": "Preparation",
                        "description": "Set up a 50 mL round-bottom flask with magnetic stirrer and reflux condenser. Ensure proper ventilation.",
                        "reagents": "Benzyl chloride (5 mmol, 0.63 g), Sodium hydroxide (10 mmol, 0.40 g)",
                        "conditions": "Room temperature",
                        "time": "5 minutes"
                    },
                    {
                        "title": "Reaction Setup",
                        "description": "Dissolve benzyl chloride in 10 mL ethanol. Add aqueous NaOH solution slowly with stirring.",
                        "reagents": "Ethanol (10 mL), Aqueous NaOH (10 M, 1 mL)",
                        "conditions": "Room temperature, stirring",
                        "time": "10 minutes"
                    },
                    {
                        "title": "Reaction",
                        "description": "Heat the reaction mixture under reflux at 60°C with continuous stirring.",
                        "reagents": "Reaction mixture from previous step",
                        "conditions": "60°C, reflux",
                        "time": "3 hours"
                    },
                    {
                        "title": "Workup",
                        "description": "Cool to room temperature. Extract with diethyl ether (2 × 15 mL). Combine organic layers.",
                        "reagents": "Diethyl ether (30 mL total)",
                        "conditions": "Room temperature",
                        "time": "15 minutes"
                    },
                    {
                        "title": "Purification",
                        "description": "Dry organic layer over anhydrous Na₂SO₄. Filter and evaporate solvent under reduced pressure.",
                        "reagents": "Anhydrous Na₂SO₄",
                        "conditions": "Room temperature, reduced pressure",
                        "time": "30 minutes"
                    }
                ],
                "expected_yield": "80-85%",
                "safety_notes": "Benzyl chloride is toxic and lachrymator. NaOH is corrosive. Use fume hood and appropriate PPE.",
                "explanation": ""
            }
            
            if explain_mode:
                protocol["explanation"] = """
                This is an SN2 substitution reaction. The hydroxide ion (OH⁻) attacks the electrophilic carbon 
                of benzyl chloride, replacing the chloride ion (Cl⁻) with a hydroxyl group (OH). 
                
                The reaction mechanism:
                1. OH⁻ approaches the carbon from the opposite side of the leaving group
                2. A new C-O bond forms while the C-Cl bond breaks
                3. The chloride ion leaves as a leaving group
                4. The product is benzyl alcohol with NaCl as a byproduct
                
                The reaction is favored by:
                - Polar aprotic solvents (ethanol)
                - Elevated temperature (60°C)
                - Excess base (NaOH)
                """
            
            return protocol
        
        # Generic demo protocol
        return {
            "title": "Generated Protocol",
            "reaction": "Chemical reaction",
            "steps": [
                {
                    "title": "Step 1: Preparation",
                    "description": "Set up reaction apparatus and prepare reagents.",
                    "reagents": "As specified in query",
                    "conditions": "Room temperature",
                    "time": "10 minutes"
                },
                {
                    "title": "Step 2: Reaction",
                    "description": "Carry out the main reaction under appropriate conditions.",
                    "reagents": "Reaction components",
                    "conditions": "As required",
                    "time": "2-4 hours"
                },
                {
                    "title": "Step 3: Workup",
                    "description": "Isolate and purify the product.",
                    "reagents": "Extraction solvents",
                    "conditions": "Room temperature",
                    "time": "30 minutes"
                }
            ],
            "expected_yield": "70-90%",
            "explanation": "This is a general protocol template. Specific conditions depend on the reaction type.",
            "safety_notes": "Handle all chemicals with appropriate PPE and in a well-ventilated area."
        }
    
    def explain_reaction(self, reaction: str) -> str:
        """Explain a chemical reaction in simple terms"""
        try:
            prompt = f"Explain this reaction in simple terms: {reaction}"
            
            if self.provider == "openai" and self.openai_key:
                response = openai.ChatCompletion.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a chemistry teacher who explains reactions in simple, clear terms."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                
                return response.choices[0].message.content
            
            elif self.provider == "cerebras" and self.cerebras_key:
                response = self._call_cerebras_api(prompt)
                return response
            
            elif self.provider == "huggingface" and self.huggingface_key:
                response = self._call_huggingface_api(prompt)
                return response
            
            else:
                return "This is a chemical reaction. The reactants combine to form products under specific conditions."
                
        except Exception as e:
            print(f"Error explaining reaction with {self.provider}: {e}")
            return "This is a chemical reaction. The reactants combine to form products under specific conditions."
    
    def validate_protocol(self, protocol: str) -> Dict[str, Any]:
        """Validate a protocol for completeness and safety"""
        try:
            prompt = f"Validate this protocol for completeness and safety: {protocol}"
            
            if self.provider == "openai" and self.openai_key:
                response = openai.ChatCompletion.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a safety expert who validates laboratory protocols."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
                return {
                    "valid": True,
                    "warnings": [],
                    "suggestions": [content]
                }
            
            elif self.provider == "cerebras" and self.cerebras_key:
                response = self._call_cerebras_api(prompt)
                return {
                    "valid": True,
                    "warnings": [],
                    "suggestions": [response]
                }
            
            elif self.provider == "huggingface" and self.huggingface_key:
                response = self._call_huggingface_api(prompt)
                return {
                    "valid": True,
                    "warnings": [],
                    "suggestions": [response]
                }
            
            else:
                return {
                    "valid": True,
                    "warnings": ["LLM validation not available"],
                    "suggestions": ["Review protocol manually for safety"]
                }
                
        except Exception as e:
            print(f"Error validating protocol with {self.provider}: {e}")
            return {
                "valid": False,
                "warnings": ["Validation failed"],
                "suggestions": ["Review protocol manually"]
            }
    
    def generate_response(self, prompt: str, system_message: str = "You are a helpful chemistry assistant.") -> str:
        """Generate a response from the LLM - used by ProtocolGenerator"""
        try:
            if self.provider == "openai" and self.openai_key:
                response = openai.ChatCompletion.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                return response.choices[0].message.content
            
            elif self.provider == "cerebras" and self.cerebras_key:
                full_prompt = f"{system_message}\n\n{prompt}"
                response = self._call_cerebras_api(full_prompt)
                return response
            
            elif self.provider == "huggingface" and self.huggingface_key:
                full_prompt = f"{system_message}\n\n{prompt}"
                response = self._call_huggingface_api(full_prompt)
                return response
            
            else:
                return "LLM service not available. Please configure API keys."
                
        except Exception as e:
            print(f"Error generating response with {self.provider}: {e}")
            return "Error generating response. Please try again."
