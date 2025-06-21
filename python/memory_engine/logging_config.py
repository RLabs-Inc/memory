"""
Enhanced logging configuration for memory system validation.

Provides detailed, colorful logging to track memory storage and retrieval.
"""

import sys
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler

# Rich console for beautiful output
console = Console()

def setup_validation_logging():
    """Configure enhanced logging for validation phase"""
    
    # Remove default handler
    logger.remove()
    
    # Add rich handler for beautiful console output
    logger.add(
        RichHandler(console=console, rich_tracebacks=True),
        format="{message}",
        level="INFO"
    )
    
    # Add file handler for detailed logs
    logger.add(
        "memory_validation.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
    )
    
    return logger

# Memory operation decorators for clear logging
def log_storage(func):
    """Decorator to log storage operations"""
    def wrapper(*args, **kwargs):
        logger.info("━" * 60)
        logger.info("📥 MEMORY STORAGE OPERATION")
        logger.info("━" * 60)
        result = func(*args, **kwargs)
        logger.info("━" * 60 + "\n")
        return result
    return wrapper

def log_retrieval(func):
    """Decorator to log retrieval operations"""
    def wrapper(*args, **kwargs):
        logger.info("━" * 60)
        logger.info("🔍 MEMORY RETRIEVAL OPERATION")
        logger.info("━" * 60)
        result = func(*args, **kwargs)
        logger.info("━" * 60 + "\n")
        return result
    return wrapper

# Export configured logger
validation_logger = setup_validation_logging()