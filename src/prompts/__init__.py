"""
Prompt templates for Catalyze agents
"""

import os
from pathlib import Path

def load_prompt(agent_name: str) -> str:
    """
    Load prompt template for a specific agent
    
    Args:
        agent_name: Name of the agent (e.g., 'automate_agent', 'research_agent')
        
    Returns:
        The prompt template as a string
    """
    prompts_dir = Path(__file__).parent
    prompt_file = prompts_dir / f"{agent_name}.txt"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def get_available_prompts() -> list:
    """
    Get list of available prompt templates
    
    Returns:
        List of available agent names
    """
    prompts_dir = Path(__file__).parent
    return [f.stem for f in prompts_dir.glob("*.txt") if f.name != "__init__.py"]
