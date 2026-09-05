"""Security utilities for kicli-code-assist.

Integrates path validation and security settings from yaml-cfg-wizard.
"""

from pathlib import Path
from typing import Optional

from yaml_cfg_wizard import PathValidator, PathSecurityError, create_validator_from_config


def get_path_validator(config: dict) -> PathValidator:
    """Get or create a path validator from configuration.
    
    Args:
        config: Configuration dict with optional security section
        
    Returns:
        PathValidator instance (may have no restrictions if not configured)
    """
    return create_validator_from_config(config)


def validate_file_path(path: str | Path, config: dict, operation: str = "read") -> Path:
    """Validate a file path against security restrictions.
    
    Args:
        path: Path to validate
        config: Configuration dict with security settings
        operation: Type of operation (read, write, delete) for error messages
        
    Returns:
        Validated Path object
        
    Raises:
        PathSecurityError: If path violates restrictions (and enforce=True)
    """
    validator = get_path_validator(config)
    try:
        return validator.validate(str(path))
    except PathSecurityError as e:
        # Re-raise with operation context
        msg = f"Security violation during {operation}: {e}"
        raise PathSecurityError(msg) from e


def is_path_allowed(path: str | Path, config: dict) -> bool:
    """Check if a path is allowed without raising.
    
    Args:
        path: Path to check
        config: Configuration dict with security settings
        
    Returns:
        True if path is allowed, False otherwise
    """
    validator = get_path_validator(config)
    return validator.is_allowed(str(path))


def get_security_info(config: dict) -> dict:
    """Get human-readable security configuration info.
    
    Args:
        config: Configuration dict
        
    Returns:
        Dict with security settings info
    """
    security = config.get("security", {})
    allowed_base = security.get("allowed_base_path")
    enforce = security.get("enforce_path_restriction", False)
    
    return {
        "enabled": bool(allowed_base),
        "allowed_base_path": allowed_base,
        "enforce": enforce,
        "mode": "enforce" if enforce else "warn",
        "description": _get_security_description(allowed_base, enforce),
    }


def _get_security_description(allowed_base: Optional[str], enforce: bool) -> str:
    """Get human-readable description of security settings.
    
    Args:
        allowed_base: Base path restriction (if any)
        enforce: Whether enforcement is enabled
        
    Returns:
        Description string
    """
    if not allowed_base:
        return "No path restrictions configured"
    
    mode = "enforced" if enforce else "warned"
    return f"File access restricted to {allowed_base} ({mode})"
