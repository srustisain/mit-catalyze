"""
Conversation Memory - Entity Extraction Layer

Lightweight entity extraction to complement LangGraph's built-in memory.
LangGraph's MemorySaver handles message history, this handles semantic entity tracking.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict


class ConversationMemory:
    """
    Entity extraction and cross-agent context sharing.
    
    Note: LangGraph's MemorySaver handles message history.
    This class focuses on extracting and tracking semantic entities
    (compounds, protocols, equipment) for cross-agent context.
    """
    
    def __init__(self):
        # Store entities per thread (not full messages - LangGraph handles that)
        self._thread_entities: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))
        self.logger = logging.getLogger("catalyze.memory")
    
    def add_message(self, thread_id: str, role: str, content: str, entities: Optional[Dict[str, List[str]]] = None):
        """
        Extract and store entities from a message.
        
        Args:
            thread_id: LangGraph thread identifier
            role: 'user' or 'assistant'
            content: Message content
            entities: Pre-extracted entities (optional)
        """
        if not thread_id or not content:
            return
        
        # Auto-extract entities if not provided
        if entities is None:
            entities = self.extract_entities(content)
        
        # Store entities (not full messages - LangGraph handles that)
        for entity_type, values in entities.items():
            self._thread_entities[thread_id][entity_type].update(values)
        
        self.logger.debug(f"Extracted entities from {role} message in thread {thread_id[:8]}... (types: {list(entities.keys())})")
    
    def get_context(self, thread_id: str) -> str:
        """
        Get formatted entity context for injection into prompts.
        
        Note: LangGraph's checkpointer handles full message history.
        This returns only the extracted entities for cross-agent context.
        
        Args:
            thread_id: LangGraph thread identifier
            
        Returns:
            Formatted context string with entities summary
        """
        if not thread_id or thread_id not in self._thread_entities:
            return ""
        
        entities = self._thread_entities[thread_id]
        if not entities:
            return ""
        
        # Format entity summary
        entity_summary = []
        if entities.get("compounds"):
            compounds = list(entities["compounds"])[:3]  # Max 3
            entity_summary.append(f"Compounds: {', '.join(compounds)}")
        if entities.get("protocols"):
            protocols = list(entities["protocols"])[:2]  # Max 2
            entity_summary.append(f"Protocols: {', '.join(protocols)}")
        if entities.get("equipment"):
            equipment = list(entities["equipment"])[:2]  # Max 2
            entity_summary.append(f"Equipment: {', '.join(equipment)}")
        
        if entity_summary:
            return "Key entities from conversation: " + "; ".join(entity_summary)
        
        return ""
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract key entities from text
        
        Returns:
            Dict with entity types as keys and lists of found entities
        """
        entities = {
            "compounds": [],
            "protocols": [],
            "equipment": []
        }
        
        if not text:
            return entities
        
        text_lower = text.lower()
        
        # Extract chemical compounds (basic patterns)
        # Look for chemical-sounding names or explicit mentions
        compound_patterns = [
            r'\b([A-Z][a-z]*(?:[- ][A-Z][a-z]*)*(?:acid|ine|ane|ene|yne|ol|one|ide|ate))\b',  # Chemical suffixes
            r'\b(aspartame|sulfuric acid|hydrochloric acid|sodium chloride|glucose|ethanol|methanol)\b',  # Common compounds
            r'\b([A-Z]{2,}[0-9]*)\b'  # Chemical formulas like H2SO4, NaCl
        ]
        
        for pattern in compound_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and len(match) > 2:
                    entities["compounds"].append(match)
        
        # Extract protocol mentions
        if any(keyword in text_lower for keyword in ["protocol", "procedure", "synthesis", "reaction", "experiment"]):
            # Look for protocol descriptions
            if "protocol for" in text_lower:
                match = re.search(r'protocol for ([^.!?]+)', text_lower)
                if match:
                    entities["protocols"].append(match.group(1).strip())
            elif "synthesis of" in text_lower:
                match = re.search(r'synthesis of ([^.!?]+)', text_lower)
                if match:
                    entities["protocols"].append(f"synthesis of {match.group(1).strip()}")
            else:
                # Generic protocol mention
                entities["protocols"].append("protocol mentioned")
        
        # Extract equipment mentions
        equipment_keywords = [
            "opentrons", "ot-2", "ot2", "robot", "pipette", "p20", "p300", "p1000",
            "plate", "well plate", "tube rack", "reservoir", "tip rack",
            "spectrophotometer", "centrifuge", "incubator", "shaker"
        ]
        
        for keyword in equipment_keywords:
            if keyword in text_lower:
                entities["equipment"].append(keyword)
        
        # Deduplicate and clean
        for key in entities:
            entities[key] = list(set([e.strip() for e in entities[key] if e.strip()]))[:5]  # Max 5 per type
        
        return entities
    
    def clear_thread(self, thread_id: str):
        """Clear entity history for a thread"""
        if thread_id in self._thread_entities:
            del self._thread_entities[thread_id]
            self.logger.info(f"Cleared thread {thread_id[:8]}...")
    
    def get_thread_summary(self, thread_id: str) -> Dict[str, Any]:
        """Get summary of entities for a thread"""
        if thread_id not in self._thread_entities:
            return {"exists": False}
        
        entities = self._thread_entities[thread_id]
        
        return {
            "exists": True,
            "entities": {k: list(v) for k, v in entities.items()},
            "entity_count": sum(len(v) for v in entities.values())
        }

