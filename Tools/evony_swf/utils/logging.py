"""Logging configuration module"""

import os
import logging
from datetime import datetime
from typing import Optional

def setup_logging(output_dir: str, level: int = logging.INFO) -> logging.Logger:
    """Configure logging with file and console output."""
    logger = logging.getLogger('evony_swf')
    logger.setLevel(level)
    
    if not logger.handlers:
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        # Create console handler
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(console_formatter)
        logger.addHandler(console)
        
        # Create file handler
        log_file = os.path.join(
            output_dir,
            f'swf_extraction_{datetime.now():%Y%m%d_%H%M%S}.log'
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
    return logger
