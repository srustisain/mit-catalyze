import requests
import json
import re
from typing import Dict, List, Optional, Any
import time

class PubChemClient:
    """Client for interacting with PubChem API"""
    
    def __init__(self):
        self.base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Catalyze-Chemistry-Assistant/1.0'
        })
    
    def extract_chemicals(self, query: str) -> List[str]:
        """Extract chemical names from a query using simple pattern matching"""
        # Common chemical patterns
        chemical_patterns = [
            r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:chloride|bromide|iodide|fluoride|oxide|hydroxide|sulfate|nitrate|acetate|alcohol|acid|amine|ether|ester|ketone|aldehyde|alkane|alkene|alkyne)\b',
            r'\b(?:benzyl|methyl|ethyl|propyl|butyl|phenyl|tolyl|naphthyl)\s+\w+\b',
            r'\b(?:sodium|potassium|calcium|magnesium|aluminum|iron|copper|zinc)\s+\w+\b',
            r'\b(?:NaOH|KOH|HCl|H2SO4|HNO3|NaCl|KCl|CaCl2|MgCl2)\b',
            r'\b(?:DMF|DMSO|THF|EtOH|MeOH|AcOH|TFA|DCM|CHCl3|CCl4)\b'
        ]
        
        chemicals = set()
        query_lower = query.lower()
        
        # Check for specific chemical names
        for pattern in chemical_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            chemicals.update(matches)
        
        # Manual extraction for common chemicals
        common_chemicals = {
            'benzyl chloride': ['benzyl chloride', 'benzylchloride'],
            'benzyl alcohol': ['benzyl alcohol', 'benzylalcohol'],
            'sodium hydroxide': ['sodium hydroxide', 'naoh', 'sodium hydroxid'],
            'ethanol': ['ethanol', 'ethyl alcohol', 'etoh'],
            'diethyl ether': ['diethyl ether', 'ether', 'ethyl ether'],
            'sodium sulfate': ['sodium sulfate', 'na2so4', 'anhydrous sodium sulfate']
        }
        
        for chemical, variations in common_chemicals.items():
            for variation in variations:
                if variation in query_lower:
                    chemicals.add(chemical)
                    break
        
        return list(chemicals)
    
    def get_chemical_data(self, chemical_name: str) -> Optional[Dict[str, Any]]:
        """Get chemical data from PubChem"""
        try:
            # Search for the compound
            cid = self._get_cid(chemical_name)
            if not cid:
                return None
            
            # Get compound properties
            properties = self._get_properties(cid)
            if not properties:
                return None
            
            # Get safety information
            safety = self._get_safety_info(cid)
            
            # Combine all data
            data = {
                'cid': cid,
                'name': chemical_name,
                'molecular_weight': properties.get('MolecularWeight'),
                'formula': properties.get('MolecularFormula'),
                'density': properties.get('Density'),
                'melting_point': properties.get('MeltingPoint'),
                'boiling_point': properties.get('BoilingPoint'),
                'cas_number': properties.get('CanonicalSMILES'),  # This would be CAS in real implementation
                'smiles': properties.get('CanonicalSMILES'),
                'hazards': safety.get('hazards', []),
                'safety_summary': safety.get('summary', '')
            }
            
            return data
            
        except Exception as e:
            print(f"Error getting data for {chemical_name}: {e}")
            return None
    
    def _get_cid(self, chemical_name: str) -> Optional[str]:
        """Get PubChem CID for a chemical name"""
        try:
            # Try compound search
            url = f"{self.base_url}/compound/name/{chemical_name}/cids/JSON"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
                    cids = data['IdentifierList']['CID']
                    return str(cids[0]) if cids else None
            
            # Try fuzzy search if exact match fails
            url = f"{self.base_url}/compound/name/{chemical_name}/cids/JSON?name_type=word"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
                    cids = data['IdentifierList']['CID']
                    return str(cids[0]) if cids else None
            
            return None
            
        except Exception as e:
            print(f"Error getting CID for {chemical_name}: {e}")
            return None
    
    def _get_properties(self, cid: str) -> Optional[Dict[str, Any]]:
        """Get chemical properties from PubChem"""
        try:
            # Get properties one by one to avoid API issues
            properties = {}
            
            # Molecular Weight
            try:
                url = f"{self.base_url}/compound/cid/{cid}/property/MolecularWeight/JSON"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        props = data['PropertyTable']['Properties'][0]
                        properties['MolecularWeight'] = props.get('MolecularWeight')
            except:
                pass
            
            # Molecular Formula
            try:
                url = f"{self.base_url}/compound/cid/{cid}/property/MolecularFormula/JSON"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        props = data['PropertyTable']['Properties'][0]
                        properties['MolecularFormula'] = props.get('MolecularFormula')
            except:
                pass
            
            # Canonical SMILES
            try:
                url = f"{self.base_url}/compound/cid/{cid}/property/CanonicalSMILES/JSON"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        props = data['PropertyTable']['Properties'][0]
                        properties['CanonicalSMILES'] = props.get('CanonicalSMILES')
            except:
                pass
            
            return properties if properties else None
            
        except Exception as e:
            print(f"Error getting properties for CID {cid}: {e}")
            return None
    
    def _get_safety_info(self, cid: str) -> Dict[str, Any]:
        """Get safety information from PubChem"""
        try:
            # This is a simplified version - in reality, you'd parse GHS data
            # For demo purposes, we'll return some basic safety info
            safety_data = {
                'hazards': [],
                'summary': ''
            }
            
            # Try to get GHS data
            url = f"{self.base_url}/compound/cid/{cid}/property/GHSClassification/JSON"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                    props = data['PropertyTable']['Properties'][0]
                    if 'GHSClassification' in props:
                        # Parse GHS data (simplified)
                        ghs_data = props['GHSClassification']
                        if isinstance(ghs_data, list):
                            for item in ghs_data:
                                if isinstance(item, dict) and 'Code' in item:
                                    safety_data['hazards'].append(item['Code'])
            
            # Add some basic safety info based on chemical type
            if not safety_data['hazards']:
                safety_data['hazards'] = self._get_basic_safety_info(cid)
            
            return safety_data
            
        except Exception as e:
            print(f"Error getting safety info for CID {cid}: {e}")
            return {'hazards': [], 'summary': ''}
    
    def _get_basic_safety_info(self, cid: str) -> List[str]:
        """Get basic safety information based on chemical type"""
        # This is a simplified safety database
        # In a real implementation, you'd have a comprehensive safety database
        
        safety_db = {
            '7503': ['Toxic', 'Skin irritant', 'Eye irritant', 'Suspected carcinogen'],  # Benzyl chloride
            '14798': ['Corrosive', 'Causes severe burns', 'Skin irritant'],  # Sodium hydroxide
            '244': ['Irritant', 'Avoid ingestion'],  # Benzyl alcohol
            '702': ['Flammable', 'Toxic if ingested'],  # Ethanol
            '3283': ['Flammable', 'Highly volatile', 'Narcotic'],  # Diethyl ether
        }
        
        return safety_db.get(cid, ['Handle with care', 'Use appropriate PPE'])
    
    def search_compounds(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for compounds by name or formula"""
        try:
            url = f"{self.base_url}/compound/name/{query}/cids/JSON"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
                    cids = data['IdentifierList']['CID'][:limit]
                    compounds = []
                    
                    for cid in cids:
                        compound_data = self.get_chemical_data_by_cid(str(cid))
                        if compound_data:
                            compounds.append(compound_data)
                    
                    return compounds
            
            return []
            
        except Exception as e:
            print(f"Error searching compounds: {e}")
            return []
    
    def get_chemical_data_by_cid(self, cid: str) -> Optional[Dict[str, Any]]:
        """Get chemical data directly by CID"""
        try:
            properties = self._get_properties(cid)
            if not properties:
                return None
            
            safety = self._get_safety_info(cid)
            
            data = {
                'cid': cid,
                'molecular_weight': properties.get('MolecularWeight'),
                'formula': properties.get('MolecularFormula'),
                'density': properties.get('Density'),
                'melting_point': properties.get('MeltingPoint'),
                'boiling_point': properties.get('BoilingPoint'),
                'smiles': properties.get('CanonicalSMILES'),
                'hazards': safety.get('hazards', []),
                'safety_summary': safety.get('summary', '')
            }
            
            return data
            
        except Exception as e:
            print(f"Error getting data for CID {cid}: {e}")
            return None


