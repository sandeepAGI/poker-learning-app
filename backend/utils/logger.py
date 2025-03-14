import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure log formatting
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Maximum log file size and backup count
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_LOG_BACKUPS = 3

# Log file paths
MAIN_LOG_FILE = os.path.join(LOGS_DIR, 'poker_app.log')
ERROR_LOG_FILE = os.path.join(LOGS_DIR, 'errors.log')
AI_DECISIONS_LOG_FILE = os.path.join(LOGS_DIR, 'ai_decisions.log')

# Setup the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Add a console handler for the root logger
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)  # Changed to DEBUG for more detailed logs
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
root_logger.addHandler(console_handler)

# Add a file handler for the main log file to the root logger
main_file_handler = RotatingFileHandler(
    MAIN_LOG_FILE, 
    maxBytes=MAX_LOG_SIZE, 
    backupCount=MAX_LOG_BACKUPS
)
main_file_handler.setLevel(logging.DEBUG)
main_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
root_logger.addHandler(main_file_handler)

# Add a file handler for error logs to the root logger
error_file_handler = RotatingFileHandler(
    ERROR_LOG_FILE, 
    maxBytes=MAX_LOG_SIZE, 
    backupCount=MAX_LOG_BACKUPS
)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
root_logger.addHandler(error_file_handler)

# Store loggers in a dictionary for reuse
LOGGERS = {}

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for the specified name.
    
    Args:
        name: The name for the logger, typically the module name
        
    Returns:
        A configured logger instance
    """
    if name in LOGGERS:
        return LOGGERS[name]
    
    logger = logging.getLogger(name)
    
    # Add a special handler for AI-related loggers
    if name.startswith('ai.'):
        ai_handler = RotatingFileHandler(
            AI_DECISIONS_LOG_FILE, 
            maxBytes=MAX_LOG_SIZE, 
            backupCount=MAX_LOG_BACKUPS
        )
        ai_handler.setLevel(logging.DEBUG)
        ai_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(ai_handler)
    
    LOGGERS[name] = logger
    return logger