"""Adapter layer to ki_core.runtime_settings for web routes and agent config.

Provides high-level API for reading/writing runtime configuration overrides.
Wraps ki_core.runtime_settings.RuntimeSettings with convenience functions
for the Flask routes in settings_routes.py and agent_config.py.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from yaml_cfg_wizard.editor import ConflictError, EditorError, ValidationError

from ki_core.runtime_settings import RuntimeSettings

__all__ = [
    "snapshot",
    "save",
    "save_secret",
    "secret_snapshot",
    "flatten",
    "settings_service",
    "ConflictError",
    "EditorError",
    "ValidationError",
]


def settings_service(project_root: Optional[Path] = None) -> RuntimeSettings:
    """Get the RuntimeSettings service for a project.
    
    Args:
        project_root: Path to project root. If None, uses current working directory.
    
    Returns:
        RuntimeSettings instance configured for the project.
    """
    if project_root is None:
        project_root = Path.cwd()
    return RuntimeSettings(project_root=project_root)


def snapshot(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """Get a snapshot of current runtime configuration state.
    
    Returns a dict with:
    - revision: opaque string identifying config version (for optimistic locking)
    - rows: list of config rows with path, value, section, overridden, editable, etc.
    
    Args:
        project_root: Path to project root. If None, uses current working directory.
    
    Returns:
        Snapshot dict containing revision and rows.
    
    Raises:
        EditorError: If configuration files cannot be read.
    """
    service = settings_service(project_root)
    return service.snapshot()


def save(
    revision: str,
    changes: Dict[str, Any],
    remove: Sequence[str],
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Save runtime configuration changes.
    
    Atomically applies changes and removals to the runtime config file,
    using optimistic locking on the revision.
    
    Args:
        revision: Opaque revision string from the snapshot (for optimistic locking).
        changes: Dict of dotted paths to new values (e.g., {"agent.streaming.state_broadcast_rate": 5}).
        remove: List of dotted paths to remove.
        project_root: Path to project root. If None, uses current working directory.
    
    Returns:
        New snapshot dict after the save.
    
    Raises:
        ConflictError: If revision has changed since snapshot (reload needed).
        ValidationError: If changes violate the schema.
        EditorError: If configuration files cannot be written.
    """
    service = settings_service(project_root)
    return service.save(revision=revision, changes=changes, remove=remove)


def save_secret(
    revision: str,
    path: str,
    value: str,
    project_root: Optional[Path] = None,
    remove: bool = False,
) -> Dict[str, Any]:
    """Save a secret configuration value (e.g., API key, token).
    
    Secrets are written to a separate secrets file (config/runtime/secrets.yaml)
    with restricted permissions.
    
    Args:
        revision: Opaque revision string from the snapshot (for optimistic locking).
        path: Dotted path to the secret (e.g., "auth.api_key").
        value: Secret value to set (or empty string if remove=True).
        project_root: Path to project root. If None, uses current working directory.
        remove: If True, remove the secret instead of saving it.
    
    Returns:
        New snapshot dict after the save.
    
    Raises:
        ConflictError: If revision has changed since snapshot (reload needed).
        ValidationError: If the path violates the schema.
        EditorError: If configuration files cannot be written.
    """
    service = settings_service(project_root)
    return service.save_secret(revision=revision, path=path, value=value, remove=remove)


def secret_snapshot(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """Get a snapshot of secret configuration state.
    
    Returns a dict with:
    - revision: opaque string identifying config version (for optimistic locking)
    - rows: list of secret rows with path, overridden, editable, etc. (values redacted)
    
    Args:
        project_root: Path to project root. If None, uses current working directory.
    
    Returns:
        Snapshot dict containing revision and rows (values masked).
    
    Raises:
        EditorError: If configuration files cannot be read.
    """
    service = settings_service(project_root)
    return service.secret_snapshot()


def flatten(section: str, nested: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a nested config dict to dotted paths.
    
    Converts nested dicts like:
        {"streaming": {"state_broadcast_rate": 5, "websocket_timeout": 30}}
    to dotted paths like:
        {"agent.streaming.state_broadcast_rate": 5, "agent.streaming.websocket_timeout": 30}
    
    This is used to prepare config updates before calling save().
    
    Args:
        section: Top-level section name (e.g., "agent", "auth").
        nested: Nested dict structure to flatten.
    
    Returns:
        Dict with dotted paths as keys.
    """
    result = {}
    
    def _flatten_recursive(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                _flatten_recursive(val, new_prefix)
        else:
            result[prefix] = obj
    
    _flatten_recursive(nested)
    return {f"{section}.{path}": val for path, val in result.items()}
