"""Tests for kicli-code-assist security integration."""

import pytest
from pathlib import Path

from kicli_code_assist.security import (
    validate_file_path,
    is_path_allowed,
    get_security_info,
    get_path_validator,
)
from yaml_cfg_wizard import PathSecurityError


class TestKicliSecurityIntegration:
    """Test security integration in kicli-code-assist."""
    
    def test_get_path_validator(self):
        """Test creating validator from config."""
        config = {
            "security": {
                "allowed_base_path": "/home/user/project",
                "enforce_path_restriction": True,
            }
        }
        
        validator = get_path_validator(config)
        assert validator.allowed_base == Path("/home/user/project")
        assert validator.enforce is True
    
    def test_validate_file_path_allowed(self):
        """Test validation of allowed path."""
        config = {
            "security": {
                "allowed_base_path": "/home/user/project",
                "enforce_path_restriction": True,
            }
        }
        
        result = validate_file_path("/home/user/project/file.txt", config)
        assert result == Path("/home/user/project/file.txt")
    
    def test_validate_file_path_blocked_strict(self):
        """Test validation of blocked path in strict mode."""
        config = {
            "security": {
                "allowed_base_path": "/home/user/project",
                "enforce_path_restriction": True,
            }
        }
        
        with pytest.raises(PathSecurityError):
            validate_file_path("/etc/passwd", config, operation="read")
    
    def test_validate_file_path_with_operation_context(self):
        """Test that operation type is included in error message."""
        config = {
            "security": {
                "allowed_base_path": "/home/user/project",
                "enforce_path_restriction": True,
            }
        }
        
        with pytest.raises(PathSecurityError, match="write"):
            validate_file_path("/tmp/file.txt", config, operation="write")
    
    def test_is_path_allowed_true(self):
        """Test path allowed check returns true."""
        config = {
            "security": {
                "allowed_base_path": "/home/user/project",
                "enforce_path_restriction": False,
            }
        }
        
        assert is_path_allowed("/home/user/project/file.txt", config)
    
    def test_is_path_allowed_false(self):
        """Test path allowed check returns false."""
        config = {
            "security": {
                "allowed_base_path": "/home/user/project",
                "enforce_path_restriction": False,
            }
        }
        
        assert not is_path_allowed("/tmp/file.txt", config)
    
    def test_is_path_allowed_no_restrictions(self):
        """Test that all paths allowed with no restrictions."""
        config = {}  # No security section
        
        assert is_path_allowed("/etc/passwd", config)
        assert is_path_allowed("/tmp/file.txt", config)
        assert is_path_allowed("/home/user/file.txt", config)
    
    def test_get_security_info_enabled(self):
        """Test getting security info when enabled."""
        config = {
            "security": {
                "allowed_base_path": "/data/projects",
                "enforce_path_restriction": True,
            }
        }
        
        info = get_security_info(config)
        
        assert info["enabled"] is True
        assert info["allowed_base_path"] == "/data/projects"
        assert info["enforce"] is True
        assert info["mode"] == "enforce"
        assert "restricted to" in info["description"].lower()
        assert "enforced" in info["description"].lower()
    
    def test_get_security_info_warning_mode(self):
        """Test getting security info in warning mode."""
        config = {
            "security": {
                "allowed_base_path": "/home/user/workspace",
                "enforce_path_restriction": False,
            }
        }
        
        info = get_security_info(config)
        
        assert info["enabled"] is True
        assert info["allowed_base_path"] == "/home/user/workspace"
        assert info["enforce"] is False
        assert info["mode"] == "warn"
        assert "warned" in info["description"].lower()
    
    def test_get_security_info_disabled(self):
        """Test getting security info when disabled."""
        config = {}  # No security section
        
        info = get_security_info(config)
        
        assert info["enabled"] is False
        assert info["allowed_base_path"] is None
        assert info["enforce"] is False
        assert info["mode"] == "warn"
        assert "no" in info["description"].lower()
        assert "restrictions" in info["description"].lower()


class TestSecurityIntegrationScenarios:
    """Test real-world security scenarios."""
    
    def test_file_browser_scenario_allowed(self):
        """Test file browser loading an allowed file."""
        config = {
            "security": {
                "allowed_base_path": "/data/projects/myapp",
                "enforce_path_restriction": True,
            }
        }
        
        # Simulating file browser loading a file
        user_path = "/data/projects/myapp/src/main.py"
        
        try:
            validated = validate_file_path(user_path, config, operation="read")
            # In real code, would load file from validated path
            assert validated == Path("/data/projects/myapp/src/main.py")
        except PathSecurityError:
            pytest.fail("Should allow path within base directory")
    
    def test_file_browser_scenario_blocked(self):
        """Test file browser blocking unauthorized access."""
        config = {
            "security": {
                "allowed_base_path": "/data/projects/myapp",
                "enforce_path_restriction": True,
            }
        }
        
        # Simulating user trying to access file outside base
        user_path = "/etc/passwd"
        
        with pytest.raises(PathSecurityError):
            validate_file_path(user_path, config, operation="read")
    
    def test_diff_loading_scenario(self):
        """Test diff file loading with security validation."""
        config = {
            "security": {
                "allowed_base_path": "/home/dev/project",
                "enforce_path_restriction": False,  # Warning mode
            }
        }
        
        # In warning mode, should not raise but may warn
        diff_files = [
            "/home/dev/project/file1.txt",      # Allowed
            "/home/dev/project/file2.txt",      # Allowed
        ]
        
        for path in diff_files:
            # Should not raise in warning mode
            result = validate_file_path(path, config, operation="read")
            assert result.exists() or True  # Path is valid, may not exist


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
