"""Logging integration for kicli-code-assist using flowpy.LoggerProxy.

This module sets up per-module loggers with the hybrid logfile strategy:
  - kicli.log              Main log
  - kicli-llm.log          LLM queries/responses
  - kicli-context.log      File loading/cache events
  - kicli-workflow.log     Approval workflow/user actions
  - kicli-errors.log       Errors only

Config-driven log levels via logconf.ini (DEBUG, INFO, WARNING, ERROR).
"""

from flowpy.loggerProxy import setup_logger

# Convenience getters for main loggers
def get_main_logger():
    """Main logger for general debugging across all components."""
    return setup_logger('kicli', 'kicli.log')

def get_llm_logger():
    """LLM-specific logger for queries, responses, provider details, URLs."""
    return setup_logger('kicli.llm', 'kicli-llm.log')

def get_context_logger():
    """Context logger for file loading, cache, deduplication events."""
    return setup_logger('kicli.context', 'kicli-context.log')

def get_workflow_logger():
    """Workflow logger for approval events and user actions."""
    return setup_logger('kicli.workflow', 'kicli-workflow.log')

def get_error_logger():
    """Error logger for exception tracking."""
    return setup_logger('kicli.errors', 'kicli-errors.log')

# Convenience module-level loggers
logger_llm = get_llm_logger()
logger_context = get_context_logger()
logger_workflow = get_workflow_logger()
logger_errors = get_error_logger()
