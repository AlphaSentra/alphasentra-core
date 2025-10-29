"""
Logging utility.
Provides file-based logging with date, unique error codes, and structured error messages.
"""

import os
import logging
import uuid
import inspect
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno >= logging.ERROR:
            color = '\033[91m'
        elif record.levelno == logging.WARNING:
            color = '\033[93m'
        elif record.levelno == logging.INFO:
            color = '\033[92m'
        else:
            color = ''
        formatted = super().format(record)
        if color:
            formatted = f"{color}{formatted}\033[0m"
        return formatted

# Ensure log directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
os.makedirs(LOG_DIR, exist_ok=True)

# Error code registry - maps error types to unique codes
ERROR_CODES = {
    # General errors
    'GENERAL': 'ERR-0001',
    'CONFIG': 'ERR-0002',
    'DATABASE': 'ERR-0003',
    'NETWORK': 'ERR-0004',
    'FILE': 'ERR-0005',
    'PERMISSION': 'ERR-0006',
    
    # AI/ML related errors
    'AI_API': 'ERR-0101',
    'AI_RESPONSE': 'ERR-0102',
    'AI_PARSING': 'ERR-0103',
    'AI_WEIGHTS': 'ERR-0104',
    
    # Cryptography errors
    'CRYPTO': 'ERR-0201',
    'ENCRYPTION': 'ERR-0202',
    'DECRYPTION': 'ERR-0203',
    
    # Data processing errors
    'DATA_PROCESSING': 'ERR-0301',
    'JSON_PARSING': 'ERR-0302',
    'DATA_VALIDATION': 'ERR-0303',
    
    # Trading/model errors
    'TRADE_LEVELS': 'ERR-0401',
    'ENTRY_PRICE': 'ERR-0402',
    'PRICE_FETCH': 'ERR-0403',
    'MODEL_EXECUTION': 'ERR-0404',
    
    # MongoDB errors
    'MONGO_CONNECTION': 'ERR-0501',
    'MONGO_OPERATION': 'ERR-0502',
    'MONGO_VALIDATION': 'ERR-0503',
    'MONGO_INSERT': 'ERR-0504',
    
    # Warning codes
    'WARNING': 'WARN-0001',
    'DATA_MISSING': 'WARN-0002',
    'CONFIG_MISSING': 'WARN-0003',
    'FALLBACK': 'WARN-0004'
}

class AgLogger:
    """Custom logger with file logging and error codes."""
    
    def __init__(self, name: str = 'alphasentra'):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create formatters
        fmt = '%(asctime)s - %(levelname)s - [%(error_code)s] - %(message)s'
        plain_formatter = logging.Formatter(fmt)
        colored_formatter = ColoredFormatter(fmt)
        
        # File handler - log to daily files
        log_file = os.path.join(LOG_DIR, f'{datetime.now().strftime("%Y-%m-%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(plain_formatter)
        
        # Console handler - for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(colored_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _get_error_code(self, error_type: str) -> str:
        """Get error code for given error type, fallback to GENERAL if not found."""
        return ERROR_CODES.get(error_type, ERROR_CODES['GENERAL'])
    
    def _generate_unique_id(self) -> str:
        """Generate a unique identifier for tracking purposes."""
        return str(uuid.uuid4())[:8]
    
    def _get_caller_info(self) -> str:
        """Get information about the calling function and script."""
        try:
            # Get the frame of the caller's caller (skip _get_caller_info and the logging method)
            frame = inspect.currentframe().f_back.f_back.f_back
            frame_info = inspect.getframeinfo(frame)
            
            # Extract script name (without path)
            script_path = frame_info.filename
            script_name = os.path.basename(script_path)
            
            # Extract function name
            function_name = frame_info.function
            
            return f"{script_name}:{function_name}()"
            
        except (AttributeError, IndexError):
            # Fallback if we can't get caller info
            return "unknown:unknown()"
    
    def error(self, message: str, error_type: str = 'GENERAL', exception: Optional[Exception] = None):
        """Log an error with unique error code and exception details."""
        error_code = self._get_error_code(error_type)
        unique_id = self._generate_unique_id()
        caller_info = self._get_caller_info()
        
        log_message = f"[{unique_id}] {message}"
        if exception:
            log_message += f" | Exception: {type(exception).__name__}: {str(exception)}"
        
        # Add caller information
        log_message += f" | From: {caller_info}"
        
        # Use extra parameter to pass error_code to formatter
        self.logger.error(log_message, extra={'error_code': error_code})
        
        # Return the error code and unique ID for reference
        return {'error_code': error_code, 'unique_id': unique_id}
    
    def warning(self, message: str, warning_type: str = 'WARNING'):
        """Log a warning with unique warning code."""
        warning_code = self._get_error_code(warning_type)
        unique_id = self._generate_unique_id()
        caller_info = self._get_caller_info()
        
        log_message = f"[{unique_id}] {message}"
        
        # Add caller information
        log_message += f" | From: {caller_info}"
        
        self.logger.warning(log_message, extra={'error_code': warning_code})
        
        return {'warning_code': warning_code, 'unique_id': unique_id}
    
    def info(self, message: str):
        """Log an informational message."""
        self.logger.info(message, extra={'error_code': 'INFO'})
    
    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message, extra={'error_code': 'DEBUG'})
    
    def critical(self, message: str, error_type: str = 'GENERAL', exception: Optional[Exception] = None):
        """Log a critical error."""
        error_code = self._get_error_code(error_type)
        unique_id = self._generate_unique_id()
        caller_info = self._get_caller_info()
        
        log_message = f"[{unique_id}] {message}"
        if exception:
            log_message += f" | Exception: {type(exception).__name__}: {str(exception)}"
        
        # Add caller information
        log_message += f" | From: {caller_info}"
        
        self.logger.critical(log_message, extra={'error_code': error_code})
        
        return {'error_code': error_code, 'unique_id': unique_id}

# Global logger instance
logger = AgLogger()

# Convenience functions for easy logging
def log_error(message: str, error_type: str = 'GENERAL', exception: Optional[Exception] = None):
    """Convenience function to log an error."""
    return logger.error(message, error_type, exception)

def log_warning(message: str, warning_type: str = 'WARNING'):
    """Convenience function to log a warning."""
    return logger.warning(message, warning_type)

def log_info(message: str):
    """Convenience function to log an info message."""
    logger.info(message)

def log_debug(message: str):
    """Convenience function to log a debug message."""
    logger.debug(message)

def log_critical(message: str, error_type: str = 'GENERAL', exception: Optional[Exception] = None):
    """Convenience function to log a critical error."""
    return logger.critical(message, error_type, exception)

# Function to get all error codes (for reference)
def get_error_codes():
    """Return all registered error codes."""
    return ERROR_CODES.copy()

# Function to initialize logging (call this at app startup)
def initialize_logging():
    """Initialize logging system - creates log directory if needed."""
    os.makedirs(LOG_DIR, exist_ok=True)
    return AgLogger()

if __name__ == "__main__":
    # Test the logging system
    initialize_logging()
    
    log_info("Logging system initialized successfully")
    log_warning("This is a test warning", "DATA_MISSING")
    log_error("This is a test error", "AI_API")
    
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        log_error("Caught test exception", "DATA_VALIDATION", e)
    
    print("Test logging completed. Check log files in:", LOG_DIR)