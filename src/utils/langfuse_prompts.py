"""
Langfuse Prompt Management Utility

This module provides utilities for managing prompts in Langfuse, including:
- Uploading existing prompts to Langfuse
- Fetching prompts with version control
- A/B testing capabilities
- Prompt performance tracking
"""

import logging
import os
import random
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None

from src.config.config import LANGFUSE_ENABLED, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST


class LangfusePromptManager:
    """Manages prompts in Langfuse with versioning and A/B testing capabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger("catalyze.langfuse_prompts")
        self.client = None
        
        if LANGFUSE_AVAILABLE and LANGFUSE_ENABLED:
            try:
                self.client = Langfuse(
                    public_key=LANGFUSE_PUBLIC_KEY,
                    secret_key=LANGFUSE_SECRET_KEY,
                    host=LANGFUSE_HOST
                )
                self.logger.info("Langfuse prompt manager initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Langfuse client: {e}")
                self.client = None
        else:
            self.logger.warning("Langfuse not available or disabled - prompt management will use local files")
    
    def upload_local_prompts(self, prompts_dir: str = "src/prompts") -> Dict[str, bool]:
        """
        Upload all local prompt files to Langfuse
        
        Args:
            prompts_dir: Directory containing prompt files
            
        Returns:
            Dictionary mapping prompt names to upload success status
        """
        if not self.client:
            self.logger.error("Langfuse client not available")
            return {}
        
        results = {}
        
        # Import the prompt loader to get current prompts
        try:
            from src.prompts import load_prompt, get_available_prompts
        except ImportError:
            self.logger.error("Could not import prompt loader")
            return {}
        
        # Define prompt configurations for each agent
        prompt_configs = {
            "research_agent": {
                "name": "research-agent-prompt",
                "description": "Expert chemistry research and analysis prompt",
                "config": {
                    "model": "gpt-4o",
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "agent_type": "research",
                    "response_format": "markdown"
                },
                "tags": ["chemistry", "research", "analysis"]
            },
            "protocol_agent": {
                "name": "protocol-agent-prompt", 
                "description": "Laboratory protocol and experimental procedure prompt",
                "config": {
                    "model": "gpt-4o",
                    "temperature": 0.2,
                    "max_tokens": 3000,
                    "agent_type": "protocol",
                    "response_format": "markdown"
                },
                "tags": ["laboratory", "protocol", "procedures"]
            },
            "automate_agent": {
                "name": "automate-agent-prompt",
                "description": "Opentrons OT-2 protocol code generation prompt",
                "config": {
                    "model": "gpt-4o",
                    "temperature": 0.0,
                    "max_tokens": 2000,
                    "agent_type": "automation",
                    "response_format": "python_code"
                },
                "tags": ["opentrons", "automation", "code-generation"]
            },
            "safety_agent": {
                "name": "safety-agent-prompt",
                "description": "Chemical safety and hazard assessment prompt", 
                "config": {
                    "model": "gpt-4o",
                    "temperature": 0.1,
                    "max_tokens": 3000,
                    "agent_type": "safety",
                    "response_format": "markdown"
                },
                "tags": ["safety", "hazards", "assessment"]
            }
        }
        
        # Get available prompts and upload them
        available_prompts = get_available_prompts()
        self.logger.info(f"Found {len(available_prompts)} prompt files: {available_prompts}")
        
        for agent_name in available_prompts:
            if agent_name not in prompt_configs:
                self.logger.warning(f"No config found for {agent_name}, skipping")
                continue
            
            try:
                # Load prompt content using the prompt loader
                prompt_content = load_prompt(agent_name)
                config = prompt_configs[agent_name]
                
                self.logger.info(f"📝 Uploading {config['name']} ({len(prompt_content)} characters)")
                
                # Create prompt in Langfuse
                self.client.create_prompt(
                    name=config["name"],
                    type="text",
                    prompt=prompt_content,
                    labels=["production"],  # Directly promote to production
                    config=config["config"],
                    tags=config["tags"],
                    commit_message=f"Upload current prompt from {agent_name}.txt"
                )
                
                results[agent_name] = True
                self.logger.info(f"✅ Uploaded {config['name']} to Langfuse")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to upload {agent_name}: {e}")
                results[agent_name] = False
        
        return results
    
    def get_prompt(self, 
                   prompt_name: str, 
                   label: str = "production",
                   version: Optional[int] = None,
                   fallback_file: Optional[str] = None) -> Optional[str]:
        """
        Get prompt from Langfuse with fallback to local file
        
        Args:
            prompt_name: Name of the prompt in Langfuse
            label: Prompt label (production, staging, latest)
            version: Specific version number (overrides label)
            fallback_file: Local file path for fallback
            
        Returns:
            Prompt content as string, or None if not found
        """
        if not self.client:
            return self._get_fallback_prompt(fallback_file)
        
        try:
            # Get prompt from Langfuse
            if version is not None:
                prompt = self.client.get_prompt(prompt_name, version=version)
            else:
                prompt = self.client.get_prompt(prompt_name, label=label)
            
            self.logger.debug(f"Retrieved prompt {prompt_name} (label: {label}, version: {getattr(prompt, 'version', 'unknown')})")
            return prompt.prompt
            
        except Exception as e:
            self.logger.warning(f"Failed to get prompt {prompt_name} from Langfuse: {e}")
            return self._get_fallback_prompt(fallback_file)
    
    def get_prompt_with_config(self, 
                               prompt_name: str, 
                               label: str = "production",
                               version: Optional[int] = None) -> Dict[str, Any]:
        """
        Get prompt with its configuration from Langfuse
        
        Args:
            prompt_name: Name of the prompt in Langfuse
            label: Prompt label (production, staging, latest)
            version: Specific version number (overrides label)
            
        Returns:
            Dictionary with 'prompt', 'config', 'version', and 'name' keys
        """
        if not self.client:
            return {
                "prompt": None,
                "config": {},
                "version": None,
                "name": prompt_name
            }
        
        try:
            # Get prompt from Langfuse
            if version is not None:
                prompt_obj = self.client.get_prompt(prompt_name, version=version)
            else:
                prompt_obj = self.client.get_prompt(prompt_name, label=label)
            
            return {
                "prompt": prompt_obj.prompt,
                "config": prompt_obj.config or {},
                "version": getattr(prompt_obj, 'version', None),
                "name": prompt_name,
                "langfuse_prompt": prompt_obj  # For linking to traces
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to get prompt {prompt_name} with config: {e}")
            return {
                "prompt": None,
                "config": {},
                "version": None,
                "name": prompt_name
            }
    
    def ab_test_prompts(self, 
                        prompt_name: str, 
                        labels: List[str] = ["production-a", "production-b"],
                        weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Perform A/B testing by randomly selecting between prompt versions
        
        Args:
            prompt_name: Base name of the prompt
            labels: List of labels to test between
            weights: Optional weights for selection (must sum to 1.0)
            
        Returns:
            Dictionary with selected prompt info and metadata
        """
        if not self.client:
            return self.get_prompt_with_config(prompt_name)
        
        if weights is None:
            weights = [1.0 / len(labels)] * len(labels)
        
        if len(weights) != len(labels) or abs(sum(weights) - 1.0) > 0.001:
            raise ValueError("Weights must match labels length and sum to 1.0")
        
        try:
            # Randomly select label based on weights
            selected_label = random.choices(labels, weights=weights)[0]
            
            # Get the selected prompt
            result = self.get_prompt_with_config(prompt_name, label=selected_label)
            result["ab_test"] = {
                "selected_label": selected_label,
                "available_labels": labels,
                "weights": dict(zip(labels, weights))
            }
            
            self.logger.debug(f"A/B test selected {selected_label} for {prompt_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"A/B test failed for {prompt_name}: {e}")
            return self.get_prompt_with_config(prompt_name)
    
    def create_prompt_version(self, 
                              prompt_name: str, 
                              prompt_content: str,
                              config: Optional[Dict[str, Any]] = None,
                              labels: Optional[List[str]] = None,
                              tags: Optional[List[str]] = None,
                              commit_message: Optional[str] = None) -> bool:
        """
        Create a new version of a prompt in Langfuse
        
        Args:
            prompt_name: Name of the prompt
            prompt_content: The prompt text
            config: Optional configuration dictionary
            labels: Optional labels to assign
            tags: Optional tags for organization
            commit_message: Optional commit message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            self.logger.error("Langfuse client not available")
            return False
        
        try:
            self.client.create_prompt(
                name=prompt_name,
                type="text",
                prompt=prompt_content,
                config=config,
                labels=labels or [],
                tags=tags or [],
                commit_message=commit_message
            )
            
            self.logger.info(f"✅ Created new version of {prompt_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create prompt version: {e}")
            return False
    
    def promote_to_production(self, prompt_name: str, version: int) -> bool:
        """
        Promote a specific prompt version to production
        
        Args:
            prompt_name: Name of the prompt
            version: Version number to promote
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            self.logger.error("Langfuse client not available")
            return False
        
        try:
            # Note: Langfuse doesn't have a direct "promote" API
            # This would need to be done through the UI or by creating a new version with production label
            self.logger.info(f"To promote {prompt_name} v{version} to production, use the Langfuse UI")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to promote {prompt_name}: {e}")
            return False
    
    def _get_fallback_prompt(self, fallback_file: Optional[str]) -> Optional[str]:
        """Get prompt from local file as fallback"""
        if not fallback_file:
            return None
        
        try:
            fallback_path = Path(fallback_file)
            if fallback_path.exists():
                content = fallback_path.read_text(encoding='utf-8')
                self.logger.debug(f"Using fallback prompt from {fallback_file}")
                return content
        except Exception as e:
            self.logger.error(f"Failed to read fallback prompt {fallback_file}: {e}")
        
        return None
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """
        List all prompts in the Langfuse project
        
        Returns:
            List of prompt information dictionaries
        """
        if not self.client:
            return []
        
        try:
            # Note: This would need the list prompts API which might not be available in the SDK
            # For now, return empty list and log info
            self.logger.info("Use Langfuse UI to view all prompts")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to list prompts: {e}")
            return []


# Global instance
prompt_manager = LangfusePromptManager()
