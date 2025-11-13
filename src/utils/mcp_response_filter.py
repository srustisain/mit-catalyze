"""
MCP Response Filter

Filters and truncates large MCP tool responses to reduce token usage.
Keeps only essential fields and limits array sizes to prevent 50K token responses.
"""

import json
import logging
from typing import Dict, Any, List, Union


class MCPResponseFilter:
    """Filter MCP tool responses to essential data only"""
    
    # Token budget per tool response (was 50K, now max 2K)
    MAX_TOKENS = 2000
    MAX_CHARS = MAX_TOKENS * 4  # Rough estimate: 4 chars per token
    
    # Limit array sizes
    MAX_ARRAY_ITEMS = 3
    MAX_STRING_LENGTH = 500
    
    # Essential fields to keep for each ChEMBL data type
    ESSENTIAL_FIELDS = {
        'molecule': [
            'pref_name', 'molecule_chembl_id', 'molecule_properties',
            'molecule_structures', 'max_phase'
        ],
        'target': [
            'pref_name', 'target_chembl_id', 'organism', 
            'target_type', 'target_components'
        ],
        'activity': [
            'standard_type', 'standard_value', 'standard_units',
            'pchembl_value', 'molecule_chembl_id'
        ],
        'assay': [
            'assay_chembl_id', 'assay_type', 'assay_organism',
            'description', 'confidence_score'
        ],
        'drug': [
            'molecule_chembl_id', 'pref_name', 'max_phase',
            'first_approval', 'indication_class'
        ]
    }
    
    # Nested fields to keep within molecule_properties
    MOLECULE_PROPERTY_FIELDS = [
        'molecular_weight', 'alogp', 'hba', 'hbd', 
        'psa', 'rtb', 'full_molformula'
    ]
    
    # Nested fields to keep within molecule_structures
    MOLECULE_STRUCTURE_FIELDS = [
        'canonical_smiles', 'standard_inchi_key'
    ]
    
    def __init__(self):
        self.logger = logging.getLogger("catalyze.mcp_filter")
    
    def filter_response(self, response: Any, tool_name: str = "") -> Any:
        """
        Filter MCP response to essential data only
        
        Args:
            response: Raw MCP tool response
            tool_name: Name of the tool that generated the response
            
        Returns:
            Filtered response with reduced token count
        """
        if not response:
            return response
        
        # Handle different response types
        if isinstance(response, dict):
            return self._filter_dict(response, tool_name)
        elif isinstance(response, list):
            return self._filter_list(response, tool_name)
        elif isinstance(response, str):
            return self._filter_string(response)
        else:
            return response
    
    def _filter_dict(self, data: Dict[str, Any], tool_name: str = "") -> Dict[str, Any]:
        """Filter dictionary responses"""
        # Detect data type from tool name or structure
        data_type = self._detect_data_type(data, tool_name)
        essential_fields = self.ESSENTIAL_FIELDS.get(data_type, [])
        
        filtered = {}
        
        # Special handling for common response structures
        if 'molecules' in data:
            # ChEMBL compound search response
            filtered['molecules'] = self._filter_list(data['molecules'][:self.MAX_ARRAY_ITEMS], 'molecule')
            if 'page_meta' in data:
                filtered['page_meta'] = {'total_count': data['page_meta'].get('total_count', 0)}
        elif 'targets' in data:
            # ChEMBL target search response
            filtered['targets'] = self._filter_list(data['targets'][:self.MAX_ARRAY_ITEMS], 'target')
        elif 'activities' in data:
            # ChEMBL activity search response
            filtered['activities'] = self._filter_list(data['activities'][:self.MAX_ARRAY_ITEMS], 'activity')
        else:
            # Generic filtering - keep only essential fields
            for key, value in data.items():
                if essential_fields and key not in essential_fields:
                    continue
                
                # Recursively filter nested structures
                if isinstance(value, dict):
                    filtered[key] = self._filter_nested_dict(key, value)
                elif isinstance(value, list):
                    filtered[key] = self._filter_list(value[:self.MAX_ARRAY_ITEMS], data_type)
                elif isinstance(value, str):
                    filtered[key] = self._filter_string(value)
                else:
                    filtered[key] = value
        
        return filtered
    
    def _filter_nested_dict(self, key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter nested dictionaries with context-specific rules"""
        filtered = {}
        
        # Special handling for molecule_properties
        if key == 'molecule_properties':
            for field in self.MOLECULE_PROPERTY_FIELDS:
                if field in data:
                    filtered[field] = data[field]
        
        # Special handling for molecule_structures
        elif key == 'molecule_structures':
            for field in self.MOLECULE_STRUCTURE_FIELDS:
                if field in data:
                    filtered[field] = data[field]
        
        # Generic nested dict - keep first 5 fields
        else:
            for i, (k, v) in enumerate(data.items()):
                if i >= 5:
                    break
                if isinstance(v, str):
                    filtered[k] = self._filter_string(v)
                elif isinstance(v, (list, dict)):
                    continue  # Skip nested collections to save tokens
                else:
                    filtered[k] = v
        
        return filtered
    
    def _filter_list(self, data: List[Any], data_type: str = "") -> List[Any]:
        """Filter list responses - limit size and filter items"""
        if not data:
            return data
        
        # Limit array size
        limited = data[:self.MAX_ARRAY_ITEMS]
        
        # Filter each item
        filtered = []
        for item in limited:
            if isinstance(item, dict):
                filtered.append(self._filter_dict(item, data_type))
            elif isinstance(item, str):
                filtered.append(self._filter_string(item))
            else:
                filtered.append(item)
        
        return filtered
    
    def _filter_string(self, text: str) -> str:
        """Truncate long strings"""
        if len(text) > self.MAX_STRING_LENGTH:
            return text[:self.MAX_STRING_LENGTH] + "..."
        return text
    
    def _detect_data_type(self, data: Dict[str, Any], tool_name: str = "") -> str:
        """Detect the data type from structure or tool name"""
        # Check tool name first
        if 'compound' in tool_name or 'molecule' in tool_name:
            return 'molecule'
        elif 'target' in tool_name:
            return 'target'
        elif 'activity' in tool_name or 'activities' in tool_name:
            return 'activity'
        elif 'assay' in tool_name:
            return 'assay'
        elif 'drug' in tool_name:
            return 'drug'
        
        # Check structure
        if 'molecule_chembl_id' in data or 'canonical_smiles' in data:
            return 'molecule'
        elif 'target_chembl_id' in data:
            return 'target'
        elif 'standard_type' in data and 'standard_value' in data:
            return 'activity'
        elif 'assay_chembl_id' in data:
            return 'assay'
        
        return 'unknown'
    
    def estimate_token_count(self, data: Any) -> int:
        """Rough estimate of token count"""
        try:
            json_str = json.dumps(data)
            # Rough estimate: 4 chars per token
            return len(json_str) // 4
        except:
            return 0
    
    def log_filtering_stats(self, original: Any, filtered: Any, tool_name: str = ""):
        """Log token reduction statistics"""
        original_tokens = self.estimate_token_count(original)
        filtered_tokens = self.estimate_token_count(filtered)
        reduction = ((original_tokens - filtered_tokens) / original_tokens * 100) if original_tokens > 0 else 0
        
        self.logger.info(
            f"MCP Response filtered ({tool_name}): "
            f"{original_tokens} → {filtered_tokens} tokens "
            f"({reduction:.1f}% reduction)"
        )

