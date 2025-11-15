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
    
    # Balanced token budget - enough info to be useful, not excessive
    MAX_TOKENS = 2000  # Increased from 300 to 2000 for useful responses
    MAX_CHARS = MAX_TOKENS * 4  # Rough estimate: 4 chars per token
    
    # Return top 3-5 results instead of just 1
    MAX_ARRAY_ITEMS = 3  # Top 3 results (was 1)
    MAX_STRING_LENGTH = 200  # Increased from 100 to 200 chars
    MAX_NESTED_DEPTH = 2  # Allow 2 levels of nesting (was 1)
    TOTAL_RESPONSE_CHAR_LIMIT = 8000  # Increased from 1500 to 8000 for useful data
    
    # Essential fields with more useful information
    ESSENTIAL_FIELDS = {
        'molecule': [
            'pref_name', 'molecule_chembl_id', 'molecule_type',
            'molecule_properties', 'molecule_structures'  # Include properties and structures
        ],
        'target': [
            'pref_name', 'target_chembl_id', 'target_type', 'organism'
        ],
        'activity': [
            'standard_type', 'standard_value', 'standard_units',
            'pchembl_value', 'activity_comment'
        ],
        'assay': [
            'assay_chembl_id', 'assay_type', 'description'
        ],
        'drug': [
            'molecule_chembl_id', 'pref_name', 'max_phase', 'indication_class'
        ]
    }
    
    # Nested fields - more useful properties
    MOLECULE_PROPERTY_FIELDS = [
        'molecular_weight', 'full_molformula', 'alogp', 'hba', 'hbd',
        'num_ro5_violations'  # Drug-likeness properties
    ]
    
    # Nested fields - keep both SMILES and InChI
    MOLECULE_STRUCTURE_FIELDS = [
        'canonical_smiles', 'standard_inchi_key'
    ]
    
    def __init__(self):
        self.logger = logging.getLogger("catalyze.mcp_filter")
    
    def filter_response(self, response: Any, tool_name: str = "") -> Any:
        """
        Filter MCP response to essential data only with aggressive size limits
        
        Args:
            response: Raw MCP tool response
            tool_name: Name of the tool that generated the response
            
        Returns:
            Filtered response with reduced token count
        """
        if not response:
            return response
        
        # Log original size for debugging
        original_tokens = self.estimate_token_count(response)
        if original_tokens > 10000:
            self.logger.warning(f"Large response detected: {original_tokens} tokens from {tool_name}")
        
        # Handle different response types with depth tracking
        if isinstance(response, dict):
            filtered = self._filter_dict(response, tool_name, depth=0)
        elif isinstance(response, list):
            filtered = self._filter_list(response, tool_name, depth=0)
        elif isinstance(response, str):
            filtered = self._filter_string(response)
        else:
            filtered = response
        
        # EMERGENCY TRUNCATION: Hard cap at 3000 chars
        filtered_str = json.dumps(filtered) if not isinstance(filtered, str) else filtered
        if len(filtered_str) > self.TOTAL_RESPONSE_CHAR_LIMIT:
            self.logger.warning(f"Emergency truncation: {len(filtered_str)} chars → {self.TOTAL_RESPONSE_CHAR_LIMIT}")
            if isinstance(filtered, dict):
                # Keep only first 2 top-level keys
                filtered = dict(list(filtered.items())[:2])
            elif isinstance(filtered, list):
                # Keep only first item
                filtered = filtered[:1]
            else:
                # Truncate string
                filtered = filtered_str[:self.TOTAL_RESPONSE_CHAR_LIMIT] + "...[truncated]"
        
        # Log reduction stats
        filtered_tokens = self.estimate_token_count(filtered)
        if original_tokens > 0:
            reduction = ((original_tokens - filtered_tokens) / original_tokens * 100)
            self.logger.info(f"Filtered {tool_name}: {original_tokens}→{filtered_tokens} tokens ({reduction:.0f}% reduction)")
        
        return filtered
    
    def _filter_dict(self, data: Dict[str, Any], tool_name: str = "", depth: int = 0) -> Dict[str, Any]:
        """Filter dictionary responses with depth tracking"""
        # Stop recursion if too deep
        if depth >= self.MAX_NESTED_DEPTH:
            return {"_truncated": f"Max depth {self.MAX_NESTED_DEPTH} reached"}
        
        # Detect data type from tool name or structure
        data_type = self._detect_data_type(data, tool_name)
        essential_fields = self.ESSENTIAL_FIELDS.get(data_type, [])
        
        filtered = {}
        
        # Special handling for common response structures
        if 'molecules' in data:
            # ChEMBL compound search response - ONLY 1 result
            filtered['molecules'] = self._filter_list(data['molecules'][:self.MAX_ARRAY_ITEMS], 'molecule', depth + 1)
            if 'page_meta' in data:
                filtered['page_meta'] = {'total_count': data['page_meta'].get('total_count', 0)}
        elif 'targets' in data:
            # ChEMBL target search response - ONLY 1 result
            filtered['targets'] = self._filter_list(data['targets'][:self.MAX_ARRAY_ITEMS], 'target', depth + 1)
        elif 'activities' in data:
            # ChEMBL activity search response - ONLY 1 result
            filtered['activities'] = self._filter_list(data['activities'][:self.MAX_ARRAY_ITEMS], 'activity', depth + 1)
        else:
            # Generic filtering - keep only essential fields
            for key, value in data.items():
                if essential_fields and key not in essential_fields:
                    continue
                
                # Recursively filter nested structures with depth check
                if isinstance(value, dict):
                    filtered[key] = self._filter_nested_dict(key, value, depth + 1)
                elif isinstance(value, list):
                    filtered[key] = self._filter_list(value[:self.MAX_ARRAY_ITEMS], data_type, depth + 1)
                elif isinstance(value, str):
                    filtered[key] = self._filter_string(value)
                else:
                    filtered[key] = value
        
        return filtered
    
    def _filter_nested_dict(self, key: str, data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """Filter nested dictionaries with context-specific rules and depth tracking"""
        # Stop recursion if too deep
        if depth >= self.MAX_NESTED_DEPTH:
            return {"_truncated": "max_depth"}
        
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
        
        # Generic nested dict - keep first 3 fields only (was 5)
        else:
            for i, (k, v) in enumerate(data.items()):
                if i >= 3:  # Reduced from 5 to 3
                    break
                if isinstance(v, str):
                    filtered[k] = self._filter_string(v)
                elif isinstance(v, (list, dict)):
                    continue  # Skip nested collections to save tokens
                else:
                    filtered[k] = v
        
        return filtered
    
    def _filter_list(self, data: List[Any], data_type: str = "", depth: int = 0) -> List[Any]:
        """Filter list responses - limit size and filter items with depth tracking"""
        if not data:
            return data
        
        # Stop recursion if too deep
        if depth >= self.MAX_NESTED_DEPTH:
            return ["_truncated_list"]
        
        # Limit array size to 1 item only
        limited = data[:self.MAX_ARRAY_ITEMS]
        
        # Filter each item
        filtered = []
        for item in limited:
            if isinstance(item, dict):
                filtered.append(self._filter_dict(item, data_type, depth + 1))
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

