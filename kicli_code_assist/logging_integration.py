"""Logging integration for kicli-code-assist using flowpy.LoggerProxy.

This module sets up per-module loggers with the hybrid logfile strategy:
  - kicli.log              Main log
  - kicli-llm.log          LLM queries/responses
  - kicli-context.log      File loading/cache events
  - kicli-workflow.log     Approval workflow/user actions
  - kicli-errors.log       Errors only

Config-driven log levels via logconf.ini (DEBUG, INFO, WARNING, ERROR).
Timestamps: HH:MM:SS format with milliseconds for precision.
"""

from flowpy.loggerProxy import setup_logger

# Log format with timestamps (HH:MM:SS only, no date)
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

# Cache loggers to avoid multiple handler setup
_loggers = {}

def _get_or_create_logger(name: str, logfile: str):
    """Get cached logger or create new one.
    
    Prevents duplicate handlers when setup_logger is called multiple times.
    """
    key = (name, logfile)
    if key not in _loggers:
        # Setup with timestamp format (HH:MM:SS.mmm)
        _loggers[key] = setup_logger(name, logfile, fmt=LOG_FORMAT)
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
