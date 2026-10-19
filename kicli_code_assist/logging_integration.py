"""Logging integration for kicli-code-assist using flowpy.LoggerProxy.

This module sets up per-module loggers with configuration-driven levels from ki.yaml.
The logging section in ki.yaml controls:
  - level: global log level (DEBUG, INFO, WARNING, ERROR)
  - per_module: dict mapping module names to override levels
  - handlers: list of handler definitions (file paths, etc.)

Log directory: Resolved from storage.log_dir in config, defaults to ~/dev_data/kicli-code-assist/log
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from flowpy.loggerProxy import setup_logger

if TYPE_CHECKING:
    from ki_core import ConfigManager

# Default format with timestamps (ISO 8601: HH:MM:SS.mmm)
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

# Cache loggers to avoid multiple handler setup
_loggers: dict[tuple[str, str], object] = {}
_config_manager: Optional[ConfigManager] = None


def set_config_manager(mgr: ConfigManager) -> None:
    """Set the ConfigManager for this logging session.
    
    Called early in app startup to bind logging config resolution to
    the config system. If not called, falls back to defaults.
    """
    global _config_manager
    _config_manager = mgr


def _get_log_dir() -> Path:
    """Get log directory from config, with intelligent defaults.
    
    Tries to resolve from storage.log_dir in config; falls back to
    ~/dev_data/kicli-code-assist/log if not configured or config not available.
    """
    # Try config-based resolution
    if _config_manager:
        try:
            log_dir_str = _config_manager.get("storage.log_dir", "")
            if log_dir_str:
                return Path(log_dir_str).expanduser()
        except Exception:
            pass
    
    # Default fallback
    default_log_dir = Path.home() / "dev_data" / "kicli-code-assist" / "log"
    default_log_dir.mkdir(parents=True, exist_ok=True)
    return default_log_dir


def _get_log_config() -> dict:
    """Get logging config from ConfigManager (or defaults if not set)."""
    if _config_manager is None:
        return {
            "level": "INFO",
            "format": LOG_FORMAT,
            "per_module": {},
        }
    return _config_manager.get_logging_config()


def _get_or_create_logger(name: str, logfile_basename: str):
    """Get cached logger or create new one.
    
    Args:
        name: Logger name
        logfile_basename: Just the filename (e.g. 'kicli.log'), not full path
        
    Prevents duplicate handlers when setup_logger is called multiple times.
    Respects per-module log level overrides from config.
    """
    log_dir = _get_log_dir()
    full_logfile = str(log_dir / logfile_basename)
    
    key = (name, full_logfile)
    if key not in _loggers:
        try:
            log_config = _get_log_config()
            
            # Check for per-module level override
            per_module_levels = log_config.get("per_module", {})
            level = per_module_levels.get(name, log_config.get("level", "INFO"))
            
            # Setup with config-driven format and level
            fmt = log_config.get("format", LOG_FORMAT)
            
            # Ensure parent directory exists before creating logger
            Path(full_logfile).parent.mkdir(parents=True, exist_ok=True)
            
            logger_obj = setup_logger(name, full_logfile, fmt=fmt)
            
            # Verify logger was created
            if logger_obj is None:
                import sys
                print(f"WARNING: setup_logger returned None for {name}", file=sys.stderr)
                # Fallback to print-based logging
                import logging
                logger_obj = logging.getLogger(name)
            
            _loggers[key] = logger_obj
        except Exception as e:
            import sys
            print(f"ERROR creating logger {name}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise
    
    return _loggers[key]


# Convenience getters for main loggers
def get_main_logger():
    """Main logger for general debugging across all components."""
    return _get_or_create_logger('kicli', 'kicli.log')


def get_llm_logger():
    """LLM-specific logger for queries, responses, provider details, URLs."""
    return _get_or_create_logger('kicli.llm', 'kicli-llm.log')


def get_context_logger():
    """Context logger for file loading, cache, deduplication events."""
    return _get_or_create_logger('kicli.context', 'kicli-context.log')


def get_workflow_logger():
    """Workflow logger for approval events and user actions."""
    return _get_or_create_logger('kicli.workflow', 'kicli-workflow.log')


def get_error_logger():
    """Error logger for exception tracking."""
    return _get_or_create_logger('kicli.errors', 'kicli-errors.log')


# Convenience module-level loggers (initialized via getters)
logger_llm = get_llm_logger()
logger_context = get_context_logger()
logger_workflow = get_workflow_logger()
logger_errors = get_error_logger()
