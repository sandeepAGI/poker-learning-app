import os
import logging
import json
import uuid
import threading
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar
from typing import Dict, Any, Optional
import sys

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Context variables for correlation tracking
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('request_context', default=None)

# Configure log formatting - JSON structured logging
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Maximum log file size and backup count
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_LOG_BACKUPS = 3

# Log file paths
MAIN_LOG_FILE = os.path.join(LOGS_DIR, 'poker_app.log')
ERROR_LOG_FILE = os.path.join(LOGS_DIR, 'errors.log')
AI_DECISIONS_LOG_FILE = os.path.join(LOGS_DIR, 'ai_decisions.log')

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation ID if available
        corr_id = correlation_id.get()
        if corr_id:
            log_entry['correlation_id'] = corr_id
            
        # Add request context if available
        req_context = request_context.get()
        if req_context:
            log_entry['request_context'] = req_context
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add any extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                           'filename', 'module', 'lineno', 'funcName', 'created', 
                           'msecs', 'relativeCreated', 'thread', 'threadName', 
                           'processName', 'process', 'getMessage', 'exc_info', 
                           'exc_text', 'stack_info']:
                log_entry[key] = value
                
        return json.dumps(log_entry, default=str)

class SimpleFormatter(logging.Formatter):
    """Simple formatter for console output"""
    
    def format(self, record: logging.LogRecord) -> str:
        corr_id = correlation_id.get()
        corr_prefix = f"[{corr_id[:8]}] " if corr_id else ""
        
        return f'{self.formatTime(record, self.datefmt)} - {corr_prefix}{record.name} - {record.levelname} - {record.getMessage()}'

# Setup the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Add a console handler for the root logger (simple format for readability)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Less verbose for console
console_handler.setFormatter(SimpleFormatter(datefmt=LOG_DATE_FORMAT))
root_logger.addHandler(console_handler)

# Add a file handler for the main log file to the root logger (structured JSON)
main_file_handler = RotatingFileHandler(
    MAIN_LOG_FILE, 
    maxBytes=MAX_LOG_SIZE, 
    backupCount=MAX_LOG_BACKUPS
)
main_file_handler.setLevel(logging.DEBUG)
main_file_handler.setFormatter(StructuredFormatter(datefmt=LOG_DATE_FORMAT))
root_logger.addHandler(main_file_handler)

# Add a file handler for error logs to the root logger (structured JSON)
error_file_handler = RotatingFileHandler(
    ERROR_LOG_FILE, 
    maxBytes=MAX_LOG_SIZE, 
    backupCount=MAX_LOG_BACKUPS
)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(StructuredFormatter(datefmt=LOG_DATE_FORMAT))
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
        ai_handler.setFormatter(StructuredFormatter(datefmt=LOG_DATE_FORMAT))
        logger.addHandler(ai_handler)
    
    LOGGERS[name] = logger
    return logger

def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())

def set_correlation_id(corr_id: str = None) -> str:
    """Set correlation ID for the current context"""
    if corr_id is None:
        corr_id = generate_correlation_id()
    correlation_id.set(corr_id)
    return corr_id

def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID"""
    return correlation_id.get()

def set_request_context(context: Dict[str, Any]):
    """Set request context for the current request"""
    request_context.set(context)

def get_request_context() -> Optional[Dict[str, Any]]:
    """Get the current request context"""
    return request_context.get()

def clear_context():
    """Clear all context variables"""
    correlation_id.set(None)
    request_context.set(None)

def log_with_context(logger: logging.Logger, level: int, msg: str, **kwargs):
    """Log a message with additional context"""
    extra = kwargs.copy()
    
    # Add correlation ID if not already present
    if 'correlation_id' not in extra:
        corr_id = get_correlation_id()
        if corr_id:
            extra['correlation_id'] = corr_id
    
    # Add request context if not already present
    if 'request_context' not in extra:
        req_context = get_request_context()
        if req_context:
            extra['request_context'] = req_context
    
    logger.log(level, msg, extra=extra)