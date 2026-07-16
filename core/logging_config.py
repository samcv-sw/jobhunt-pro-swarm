# ──────────────────────────────────────────────────────────────────────────────
# logging_config.py - Centralized Structured Logging Configuration
# Provides JSON-formatted logging for production, pretty-printing for development
# ──────────────────────────────────────────────────────────────────────────────

import json
import logging
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Pretty formatter with colors for development."""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
        "RESET": "\033[0m",
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        
        record.levelname = f"{color}{record.levelname}{reset}"
        record.name = f"{color}{record.name}{reset}"
        
        return super().format(record)


def setup_logging(is_production=False):
    """Configure logging for the application."""
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if is_production:
        formatter = JSONFormatter()
        log_format = "%(message)s"
    else:
        formatter = ColoredFormatter(
            fmt="[%(asctime)s] %(levelname)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        log_format = "%(message)s"
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (production)
    if is_production:
        try:
            file_handler = logging.FileHandler("logs/app.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Could not set up file logging: {e}")
    
    return root_logger


# Application-specific loggers
APP_LOGGER = logging.getLogger("app")
DB_LOGGER = logging.getLogger("database")
SECURITY_LOGGER = logging.getLogger("security")
PERFORMANCE_LOGGER = logging.getLogger("performance")
