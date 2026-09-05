#!/usr/bin/env python3
"""
Example: Using path security in kicli-code-assist

This script demonstrates how to:
1. Configure security settings
2. Validate file paths
3. Handle security violations
"""

from pathlib import Path
from yaml_cfg_wizard import PathValidator, PathSecurityError
from kicli_code_assist.security import (
    validate_file_path,
    is_path_allowed,
    get_security_info,
)


def example_1_basic_validation():
    """Example 1: Basic path validation."""
    print("\n=== Example 1: Basic Path Validation ===")
    
    config = {
        "security": {
            "allowed_base_path": "/data/projects/myapp",
            "enforce_path_restriction": False,  # Warning mode
        }
    }
    
    # Test various paths
    test_paths = [
        "/data/projects/myapp/src/main.py",      # ✅ Allowed
        "/data/projects/myapp/config/config.yaml", # ✅ Allowed
        "/etc/passwd",                           # ❌ Blocked
        "/tmp/upload.zip",                       # ❌ Blocked
    ]
    
    for path in test_paths:
        allowed = is_path_allowed(path, config)
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"  {status}: {path}")


def example_2_strict_enforcement():
    """Example 2: Strict enforcement mode."""
    print("\n=== Example 2: Strict Enforcement Mode ===")
    
    config = {
        "security": {
            "allowed_base_path": "/data/projects/myapp",
            "enforce_path_restriction": True,  # Strict mode
        }
    }
    
    # Allowed path succeeds
    try:
        result = validate_file_path("/data/projects/myapp/file.txt", config)
        print(f"  ✅ Validated: {result}")
    except PathSecurityError as e:
        print(f"  ❌ Error: {e}")
    
    # Blocked path raises exception
    try:
        result = validate_file_path("/tmp/file.txt", config)
        print(f"  ✅ Validated: {result}")
    except PathSecurityError as e:
        print(f"  ❌ Error: {e}")


def example_3_directory_traversal_prevention():
    """Example 3: Prevention of directory traversal attacks."""
    print("\n=== Example 3: Directory Traversal Prevention ===")
    
    validator = PathValidator(
        allowed_base_path="/data/projects/myapp",
        enforce=False
    )
    
    # Attempted escape paths
    escape_attempts = [
        "/data/projects/myapp/../../etc/passwd",     # .. escape
        "/data/projects/myapp/./../../secret.key",   # ./ and .. escape
        "/data/projects/../other/file.txt",          # Parent directory escape
    ]
    
    print("  Attempting to escape /data/projects/myapp:")
    for path in escape_attempts:
        allowed = validator.is_allowed(path)
        status = "ESCAPED" if allowed else "BLOCKED"
        print(f"    {status}: {path}")


def example_4_relative_paths():
    """Example 4: Working with relative paths."""
    print("\n=== Example 4: Relative Path Handling ===")
    
    validator = PathValidator(allowed_base_path="/data/projects/myapp")
    
    # Relative paths are converted to absolute
    test_paths = [
        "file.txt",
        "src/main.py",
        "config/settings.yaml",
    ]
    
    print("  Relative paths (base: /data/projects/myapp):")
    for path in test_paths:
        relative = validator.make_relative(
            Path("/data/projects/myapp") / path
        )
        print(f"    {relative}")


def example_5_config_info():
    """Example 5: Getting security configuration info."""
    print("\n=== Example 5: Security Configuration Info ===")
    
    configs = [
        {
            "name": "Strict (production)",
            "config": {
                "security": {
                    "allowed_base_path": "/data/projects",
                    "enforce_path_restriction": True,
                }
            },
        },
        {
            "name": "Warning mode (development)",
            "config": {
                "security": {
                    "allowed_base_path": "/home/user/workspace",
                    "enforce_path_restriction": False,
                }
            },
        },
        {
            "name": "No restrictions (default)",
            "config": {},
        },
    ]
    
    for item in configs:
        info = get_security_info(item["config"])
        print(f"\n  {item['name']}:")
        print(f"    Enabled: {info['enabled']}")
        print(f"    Base path: {info['allowed_base_path']}")
        print(f"    Mode: {info['mode']}")
        print(f"    {info['description']}")


def example_6_file_browser_integration():
    """Example 6: Integration in file browser (pseudo-code)."""
    print("\n=== Example 6: File Browser Integration (Pseudo-Code) ===")
    
    code = '''
def load_file_in_browser(file_path: str, config: dict) -> Optional[str]:
    """Load file in browser with security validation."""
    try:
        # Validate path against security settings
        validated_path = validate_file_path(file_path, config, operation="read")
        
        # Read and display file content
        with open(validated_path) as f:
            content = f.read()
        
        return content
    
    except PathSecurityError as e:
        # Handle security violation
        if config.get("security", {}).get("enforce_path_restriction"):
            show_error(f"Access denied: {e}")
            return None
        else:
            show_warning(f"Security warning: {e}")
            # May still return content in warning mode
            return None
    
    except FileNotFoundError:
        show_error("File not found")
        return None
'''
    
    print(code)


def main():
    """Run all examples."""
    print("=" * 60)
    print("Path Security Examples")
    print("=" * 60)
    
    example_1_basic_validation()
    example_2_strict_enforcement()
    example_3_directory_traversal_prevention()
    example_4_relative_paths()
    example_5_config_info()
    example_6_file_browser_integration()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
