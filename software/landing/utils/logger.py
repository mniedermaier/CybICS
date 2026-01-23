"""
Logging configuration module for CybICS application
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name='CybICS', level=logging.INFO, log_file='app.log', max_bytes=10*1024*1024, backup_count=3):
    """
    Set up a logger with both console and file handlers.

    Args:
        name: Logger name
        level: Logging level
        log_file: Path to log file
        max_bytes: Maximum log file size before rotation (default 10MB)
        backup_count: Number of backup files to keep

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")

    return logger

# Create the main application logger
logger = setup_logger()
