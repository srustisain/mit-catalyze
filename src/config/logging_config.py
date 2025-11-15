"""
Centralized logging configuration for Catalyze
"""

import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", log_to_file: bool = False, log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration for the entire application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to a file in addition to console
        log_file: Path to log file (if log_to_file is True)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file and log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    logging.getLogger('langgraph').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Flask HTTP logs
    
    # Set Catalyze component log levels
    # Only show INFO and above for most components
    logging.getLogger('catalyze.researchagent').setLevel(logging.INFO)
    logging.getLogger('catalyze.protocolagent').setLevel(logging.INFO)
    logging.getLogger('catalyze.automateagent').setLevel(logging.INFO)
    logging.getLogger('catalyze.safetyagent').setLevel(logging.INFO)
    logging.getLogger('catalyze.smart_router').setLevel(logging.INFO)
    logging.getLogger('catalyze.intent_classifier').setLevel(logging.INFO)
    logging.getLogger('catalyze.pipeline').setLevel(logging.INFO)
    logging.getLogger('catalyze.api').setLevel(logging.INFO)
    logging.getLogger('catalyze.flask').setLevel(logging.INFO)
    
    # Reduce noise from filtering (only show warnings and errors)
    logging.getLogger('catalyze.mcp_filter').setLevel(logging.WARNING)
    
    # Keep validation logs visible
    logging.getLogger('catalyze.opentrons_validator').setLevel(logging.INFO)
    
    # Log the configuration
    logging.info(f"Logging configured - Level: {level}, File: {log_file if log_to_file else 'None'}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

# Initialize logging on import
setup_logging()

