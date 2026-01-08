"""
Structured logging configuration.
"""
import logging
import sys
from typing import Dict, Any
from pythonjsonlogger import jsonlogger
from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['service'] = settings.APP_NAME
        log_record['environment'] = settings.ENVIRONMENT
        log_record['level'] = record.levelname
        log_record['logger_name'] = record.name
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_record.update(record.extra)


def setup_logging():
    """Configure application logging."""
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatter for production, simple formatter for development
    if settings.is_production:
        formatter = CustomJsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            rename_fields={'asctime': 'timestamp'}
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set levels for noisy libraries
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    logging.getLogger('motor').setLevel(logging.WARNING)
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    root_logger.info(
        "Logging configured",
        extra={"log_level": settings.LOG_LEVEL, "environment": settings.ENVIRONMENT}
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)