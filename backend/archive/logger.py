import logging
import os
import sys
from typing import Optional


class Logger:
    """
    Centralized logging system for the poker application.
    Handles logging configuration and provides access to loggers.
    """
    # Singleton instance
    _instance = None
    
    # Logger instances by name
    _loggers = {}
    
    # Log format
    _LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # Log levels dictionary for easy reference
    LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the logging system if not already initialized."""
        if self._initialized:
            return
            
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Create console handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(self._LOG_FORMAT))
        root_logger.addHandler(console)
        
        # Create log directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Create file handler for all logs
        all_file = logging.FileHandler("logs/poker_app.log")
        all_file.setLevel(logging.INFO)
        all_file.setFormatter(logging.Formatter(self._LOG_FORMAT))
        root_logger.addHandler(all_file)
        
        # Create file handler for errors
        error_file = logging.FileHandler("logs/errors.log")
        error_file.setLevel(logging.ERROR)
        error_file.setFormatter(logging.Formatter(self._LOG_FORMAT))
        root_logger.addHandler(error_file)
        
        # Create file handler for AI decisions
        ai_file = logging.FileHandler("logs/ai_decisions.log")
        ai_file.setLevel(logging.DEBUG)
        ai_file.setFormatter(logging.Formatter(self._LOG_FORMAT))
        
        # Create AI logger specifically for AI related logging
        ai_logger = logging.getLogger("ai")
        ai_logger.setLevel(logging.DEBUG)
        ai_logger.addHandler(ai_file)
        ai_logger.propagate = False  # Don't propagate to root logger
        
        self._initialized = True
        
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger by name, creating it if it doesn't exist.
        
        Args:
            name: The name of the logger
            
        Returns:
            The logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]
    
    def set_level(self, level: str, logger_name: Optional[str] = None) -> None:
        """
        Set the logging level.
        
        Args:
            level: The level to set ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            logger_name: The specific logger to set, or None for the root logger
        """
        if level not in self.LEVELS:
            raise ValueError(f"Invalid log level: {level}")
            
        log_level = self.LEVELS[level]
        
        if logger_name:
            logger = self.get_logger(logger_name)
            logger.setLevel(log_level)
        else:
            # Set for root logger
            logging.getLogger().setLevel(log_level)


# Create a singleton instance
logger = Logger()

# Function to easily get a logger
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name for the logger
        
    Returns:
        The logger instance
    """
    return logger.get_logger(name)