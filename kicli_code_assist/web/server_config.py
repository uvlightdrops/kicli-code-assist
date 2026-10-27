"""Configuration and setup helpers for Flask server."""

import os
import logging
from pathlib import Path
from typing import Dict, Any

from kicli_code_assist.logging_integration import _get_or_create_logger, _get_log_dir
from ki_core.config import ConfigManager


def get_config() -> Dict[str, Any]:
    """Load configuration from ki.yaml via ConfigManager.
    
    Returns:
        Configuration dict with web, storage, llm, etc. settings.
        Fallback to defaults if config file not found.
    """
    try:
        config_manager = ConfigManager()
        config = config_manager.load()
        return config
    except Exception as e:
        logger = logging.getLogger("kicli-web")
        logger.error(f"Failed to load config: {e}")
        return {
            "web": {"host": "127.0.0.1", "port": 8000},
            "storage": {"log_dir": str(Path.home() / "dev_data" / "kicli-code-assist" / "log")},
        }


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """Setup logging directory and get logger.
    
    Args:
        config: Configuration dict from get_config()
        
    Returns:
        Configured logger instance
    """
    log_dir = _get_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    logger = _get_or_create_logger("kicli-web", "kicli-web.log")
    return logger


def get_cors_origins(config: Dict[str, Any]) -> list[str]:
    """Get CORS allowed origins from config.
    
    Args:
        config: Configuration dict
        
    Returns:
        List of allowed CORS origins
    """
    return config.get("web", {}).get("cors_origins", ["http://localhost:3000"])


def get_web_settings(config: Dict[str, Any]) -> tuple[str, int]:
    """Get web server host and port from config.
    
    Args:
        config: Configuration dict
        
    Returns:
        Tuple of (host, port)
    """
    web_config = config.get("web", {})
    host = web_config.get("host", "127.0.0.1")
    port = web_config.get("port", 8000)
    return host, port
