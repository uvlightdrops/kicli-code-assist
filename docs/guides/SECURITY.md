# Security Feature - Path Restriction

**Status:** 🚧 In Progress  
**Feature:** Absolute Path Security Setting  
**Last Updated:** 2026-09-05

## Overview

The security feature restricts file operations to a configured base directory, preventing directory traversal attacks and unauthorized access outside the allowed scope.

## Configuration

### Schema Section

The security settings are defined in the schema under `security`:

```yaml
security:
  # Absolute path that defines the boundary for file operations
  # File operations must not escape this directory
  allowed_base_path: "/home/user/project"
  
  # Whether to enforce restrictions (true) or warn only (false)
  enforce_path_restriction: false
```

### Configuration Examples

**Strict Enforcement (Production):**
```yaml
security:
  allowed_base_path: "/data/projects/myapp"
  enforce_path_restriction: true
```

**Warning Mode (Development):**
```yaml
security:
  allowed_base_path: "/home/user/workspace"
  enforce_path_restriction: false
```

**No Restrictions (Default):**
```yaml
# security section omitted or empty
```

## Usage

### Python API

```python
from kicli_code_assist.security import (
    validate_file_path,
    is_path_allowed,
    get_security_info,
)

# Check if path is allowed
if is_path_allowed("/data/projects/myapp/file.txt", config):
    # Path is safe
    pass

# Validate and get absolute path
try:
    validated_path = validate_file_path(
        "/data/projects/myapp/file.txt",
        config,
        operation="read"
    )
except PathSecurityError as e:
    print(f"Security violation: {e}")

# Get security configuration info
info = get_security_info(config)
print(f"Security enabled: {info['enabled']}")
print(f"Base path: {info['allowed_base_path']}")
print(f"Mode: {info['mode']}")  # 'enforce' or 'warn'
```

### CLI Usage (via yaml-cfg-wizard)

```bash
# Show security settings
yaml-cfg config show security

# Validate a specific path
python -c "
from yaml_cfg_wizard import PathValidator
from kicli_code_assist.security import is_path_allowed

validator = PathValidator(
    allowed_base_path='/data/projects/myapp',
    enforce=True
)
print(validator.is_allowed('/data/projects/myapp/file.txt'))  # True
print(validator.is_allowed('/tmp/file.txt'))  # False
"
```

## Security Guarantees

### What Is Prevented

1. **Directory Traversal Attacks**
   ```python
   # NOT allowed if base = /data/projects/myapp
   "/data/projects/myapp/../../etc/passwd"  # Rejected
   "/data/projects/../other/secret.key"     # Rejected
   ```

2. **Symlink Escape Attempts**
   - All paths are normalized and resolved
   - Symlinks outside base are rejected

3. **Absolute Path Escape**
   ```python
   # NOT allowed if base = /data/projects/myapp
   "/etc/passwd"                # Different branch
   "/home/user/other/file.txt"  # Different directory
   ```

### What Is Allowed

1. **Paths Within Base**
   ```python
   # ALLOWED if base = /data/projects/myapp
   "/data/projects/myapp/file.txt"
   "/data/projects/myapp/src/main.py"
   "/data/projects/myapp/config/settings.yaml"
   ```

2. **Relative Paths (converted to absolute)**
   ```python
   # ALLOWED if base = /data/projects/myapp
   "file.txt"                  # → /data/projects/myapp/file.txt
   "src/main.py"              # → /data/projects/myapp/src/main.py
   "../other"                 # → /data/projects/other (depends on context)
   ```

## Enforcement Modes

### Strict Mode (enforce=true)

File operations that violate restrictions **raise an exception**:

```python
validator = PathValidator(
    allowed_base_path="/data/projects/myapp",
    enforce=True
)

# Raises PathSecurityError
validator.validate("/etc/passwd")
```

**Use Case:** Production environments, sensitive operations.

### Warning Mode (enforce=false)

File operations that violate restrictions **emit a warning** but continue:

```python
import warnings
warnings.simplefilter("always")

validator = PathValidator(
    allowed_base_path="/data/projects/myapp",
    enforce=False
)

# Emits UserWarning but returns the path
path = validator.validate("/etc/passwd")
```

**Use Case:** Development, debugging, gradual rollout.

## Integration Points

### File Browser

When user selects a file in the file browser:
1. Validate path before loading
2. Reject or warn based on enforcement mode
3. Log the validation attempt

### Diff/Context Loading

When loading diff or context files:
1. Validate each file path
2. Skip or error based on enforcement mode
3. Report to user if files were blocked

### CLI File Operations

When CLI commands access files:
1. Validate input paths
2. Validate output paths
3. Clear error messages for violations

## Testing

### Test Coverage

The path validator has 13 comprehensive tests:

- ✅ No restrictions (unrestricted access)
- ✅ Allowed base path enforcement
- ✅ Strict enforcement vs warning mode
- ✅ Path normalization (./, ../)
- ✅ Relative path conversion
- ✅ Empty base path handling
- ✅ Invalid relative base path rejection
- ✅ Warning emission
- ✅ Config-based validator creation
- ✅ Real filesystem integration

Run tests:
```bash
cd yaml-cfg-wizard
python -m pytest tests/test_path_validator.py -v
```

### Manual Testing

```bash
# Test with Python REPL
python -c "
from yaml_cfg_wizard import PathValidator

v = PathValidator('/data/projects/myapp', enforce=True)

# Test allowed paths
print('Allowed:', v.is_allowed('/data/projects/myapp/file.txt'))

# Test blocked paths
print('Blocked:', v.is_allowed('/tmp/file.txt'))

# Test path normalization
print('Normalized:', v.validate('/data/projects/myapp/./src/../file.txt'))
"
```

## Deployment Considerations

### Gradual Rollout

1. **Phase 1: Monitoring**
   - Deploy with `enforce_path_restriction: false`
   - Review warning logs for violations
   - Identify problematic file operations

2. **Phase 2: Enforce**
   - Switch to `enforce_path_restriction: true`
   - Ensure all file operations are within allowed path
   - Handle PathSecurityError appropriately

3. **Phase 3: Hardening**
   - Tighten `allowed_base_path` if needed
   - Add additional path validation layers
   - Document any necessary exceptions

### Environment Configuration

```bash
# Via environment variable
export KICLI_SECURITY_ALLOWED_BASE_PATH="/data/projects"
export KICLI_SECURITY_ENFORCE_PATH_RESTRICTION="true"

# Via YAML config
cat > ki.yaml <<EOF
security:
  allowed_base_path: "/data/projects"
  enforce_path_restriction: true
EOF

# Via runtime configuration
kicli-assist config set security.allowed_base_path "/data/projects"
kicli-assist config set security.enforce_path_restriction true
```

## Error Handling

### PathSecurityError

Raised when a path violates restrictions in enforce mode:

```python
from yaml_cfg_wizard import PathSecurityError

try:
    validator.validate("/etc/passwd")
except PathSecurityError as e:
    print(f"Security violation: {e}")
    # Handle the violation appropriately
```

### Error Messages

```
Path '/etc/passwd' escapes allowed base '/data/projects/myapp'. 
All file operations must stay within the allowed directory.
```

## Future Enhancements

- [ ] Multiple allowed paths (whitelist)
- [ ] Path exceptions/exclusions
- [ ] Operation-specific restrictions (read vs write)
- [ ] Rate limiting on violations
- [ ] Audit logging of all path validations
- [ ] TUI settings panel for security configuration
- [ ] CLI command for testing path validation

## Related Documentation

- [CONFIG_CLI.md](./CONFIG_CLI.md) - Config system documentation
- [FEATURE_STATUS.md](./FEATURE_STATUS.md) - Overall feature tracking
- [ki-core CONFIG_GUIDE.md](../../ki-core/CONFIG_GUIDE.md) - Schema documentation
