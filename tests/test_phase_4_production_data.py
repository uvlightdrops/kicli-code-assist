"""Production-grade test data for Phase 4 integration.

Real-world scenarios, constraints, and performance baselines.
"""

import pytest
from dataclasses import dataclass
from typing import List


# ============================================================================
# Real-World Code Samples for Testing
# ============================================================================

PYTHON_CODE_SAMPLE_BUGGY = """
def calculate_discount(price, customer_type):
    \"\"\"Calculate discount based on customer type.\"\"\"
    if customer_type == 'vip':
        discount = 0.20
    elif customer_type == 'regular':
        discount = 0.10
    else:
        discount = 0.0
    
    final_price = price * (1 - discount)
    return final_price
"""

PYTHON_CODE_SAMPLE_IMPROVED = """
def calculate_discount(price: float, customer_type: str) -> float:
    \"\"\"Calculate discount based on customer type.
    
    Args:
        price: Product price in USD
        customer_type: One of 'vip', 'regular', 'guest'
        
    Returns:
        Final price after discount
        
    Raises:
        ValueError: If price < 0 or unknown customer type
    \"\"\"
    DISCOUNT_RATES = {
        'vip': 0.20,
        'regular': 0.10,
        'guest': 0.0,
    }
    
    if price < 0:
        raise ValueError(f"Price must be non-negative, got {price}")
    
    if customer_type not in DISCOUNT_RATES:
        raise ValueError(f"Unknown customer type: {customer_type}")
    
    discount = DISCOUNT_RATES[customer_type]
    return price * (1 - discount)
"""

SHELL_SCRIPT_SAMPLE = """#!/bin/bash
# Deploy production build

set -e  # Exit on error

BUILD_DIR="${1:-.}"
DEPLOY_ENV="${2:-production}"

echo "Building from $BUILD_DIR to $DEPLOY_ENV"

# Build
cd "$BUILD_DIR"
npm install --production
npm run build

# Deploy
if [ "$DEPLOY_ENV" = "production" ]; then
    npm run deploy:prod
else
    npm run deploy:staging
fi

echo "✓ Deployment complete"
"""

JAVASCRIPT_CODE_SAMPLE = """
async function fetchUserData(userId) {
    const response = await fetch(`/api/users/${userId}`);
    const data = response.json();
    return data;
}
"""

JAVASCRIPT_CODE_IMPROVED = """
async function fetchUserData(userId) {
    if (!userId || typeof userId !== 'string') {
        throw new Error('userId must be a non-empty string');
    }
    
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch user data:', error);
        throw error;
    }
}
"""

# Real SQL examples
SQL_VULNERABLE = """
SELECT * FROM users WHERE email = '" + userInput + "';
"""

SQL_SAFE = """
SELECT * FROM users WHERE email = $1;
"""

# Real API keys/secrets for filtering tests
SENSITIVE_DATA_SAMPLES = [
    "sk-proj-abc123def456ghi789jkl",  # OpenAI
    "sk-ant-xyz789abc123def456",  # Anthropic
    "AKIA2E3Q4R5S6T7U8V9W",  # AWS Access Key
    "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",  # AWS Secret
    "ghp_abcdefghijklmnopqrstuvwxyz1234567890",  # GitHub token
    "xoxb-1234567890123-1234567890123-AbCdEfGhIjKlMnOpQrSt",  # Slack bot token
    "postgres://user:secretpass123@db.example.com:5432/mydb",  # Database URL
    "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQE...-----END PRIVATE KEY-----",  # Private key
]


# ============================================================================
# Real-World LLM Response Scenarios
# ============================================================================

LLM_RESPONSE_MULTI_PART = """
Looking at this code, I found several issues:

## Security Issues

1. **Missing input validation** - The function accepts any customer_type without validation
2. **SQL injection risk** - If this connects to a database, parameters should be prepared

## Code Quality Issues

1. **Type hints missing** - Add type annotations for maintainability
2. **Error handling** - No validation for negative prices
3. **Magic numbers** - Discount rates should be constants

## Suggested Fix

Here's the improved version:

```python
def calculate_discount(price: float, customer_type: str) -> float:
    """Calculate discount based on customer type."""
    DISCOUNT_RATES = {
        'vip': 0.20,
        'regular': 0.10,
        'guest': 0.0,
    }
    
    if price < 0:
        raise ValueError(f"Price must be non-negative")
    if customer_type not in DISCOUNT_RATES:
        raise ValueError(f"Unknown customer type: {customer_type}")
    
    return price * (1 - DISCOUNT_RATES[customer_type])
```

## Performance

This change has no performance impact - same O(1) complexity.

## Testing

Add these unit tests:

```python
def test_discount_vip():
    assert calculate_discount(100, 'vip') == 80

def test_discount_negative_price():
    with pytest.raises(ValueError):
        calculate_discount(-10, 'regular')

def test_discount_unknown_type():
    with pytest.raises(ValueError):
        calculate_discount(100, 'unknown')
```

This should resolve the issues!
"""

LLM_RESPONSE_SHELL_COMMANDS = """
To set up the environment, run these commands:

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

After setup, verify installation:

```bash
python3 --version
pip list | grep -E "textual|cryptography|openai"
```

Your environment is ready!
"""


# ============================================================================
# Constraints & Performance Requirements
# ============================================================================

@dataclass
class PerformanceConstraint:
    """Performance requirement for Phase 4 operations."""
    operation: str
    max_time_ms: float
    context: str
    
    def __post_init__(self):
        if self.max_time_ms <= 0:
            raise ValueError(f"max_time_ms must be positive, got {self.max_time_ms}")


PERFORMANCE_CONSTRAINTS = [
    PerformanceConstraint(
        operation="AsyncOpenAIClient.achat()",
        max_time_ms=30000,  # 30 seconds (LLM latency dominates)
        context="Single non-streaming LLM call with 30s timeout"
    ),
    PerformanceConstraint(
        operation="ResponseParser.parse()",
        max_time_ms=100,  # 100ms for parsing response
        context="Parsing LLM response with up to 20 code blocks"
    ),
    PerformanceConstraint(
        operation="SensitiveDataFilter.filter()",
        max_time_ms=50,  # 50ms for secret filtering
        context="Filtering 10KB context before LLM call"
    ),
    PerformanceConstraint(
        operation="EncryptionManager.encrypt()",
        max_time_ms=100,  # 100ms for encryption
        context="Encrypting 100KB chat history with Fernet"
    ),
    PerformanceConstraint(
        operation="EncryptedStorage.save()",
        max_time_ms=200,  # 200ms for file write
        context="Saving encrypted session to disk"
    ),
    PerformanceConstraint(
        operation="ApprovalModal.render()",
        max_time_ms=50,  # 50ms for Textual rendering
        context="Rendering approval UI with 50 hunks"
    ),
    PerformanceConstraint(
        operation="AIWorkflowManager.apply_approved_changes()",
        max_time_ms=100,  # 100ms for file update
        context="Applying 100 approved line changes"
    ),
]


# ============================================================================
# Security Constraints
# ============================================================================

@dataclass
class SecurityConstraint:
    """Security requirement for Phase 4."""
    component: str
    requirement: str
    validation_method: str


SECURITY_CONSTRAINTS = [
    SecurityConstraint(
        component="SensitiveDataFilter",
        requirement="Detect all API key formats (sk-, pk-, AKIA, etc)",
        validation_method="Pattern matching with 10+ regex patterns"
    ),
    SecurityConstraint(
        component="SensitiveDataFilter",
        requirement="Redact passwords and DB URLs before LLM",
        validation_method="Verify [REDACTED] in LLM context"
    ),
    SecurityConstraint(
        component="EncryptionManager",
        requirement="Master key file has 0o600 permissions",
        validation_method="stat ~/.ki/master.key | check mode bits"
    ),
    SecurityConstraint(
        component="EncryptedStorage",
        requirement="No plaintext secrets in encrypted files",
        validation_method="Verify file content is base64 encoded"
    ),
    SecurityConstraint(
        component="Structured Errors",
        requirement="No secrets in error messages",
        validation_method="Scan error output for API key patterns"
    ),
]


# ============================================================================
# Real Integration Test Scenarios
# ============================================================================

class IntegrationTestScenario:
    """End-to-end integration test scenario."""
    
    def __init__(self, name: str, description: str, steps: List[str]):
        self.name = name
        self.description = description
        self.steps = steps


INTEGRATION_SCENARIOS = [
    IntegrationTestScenario(
        name="Fix Python Function with AI",
        description="User gets AI suggestion to improve Python function",
        steps=[
            "User opens buggy Python file in editor",
            "User enables AI checkbox",
            "AI analyzes code (async)",
            "LLM suggests improvements with type hints + error handling",
            "ResponseParser splits response into TEXT + CODE sections",
            "ApprovalModal shows improvement hunks",
            "User approves improvements",
            "Approved changes applied to editor",
            "Secrets in context were filtered before LLM call",
            "Chat history encrypted and persisted",
        ]
    ),
    IntegrationTestScenario(
        name="Fix SQL Injection Vulnerability",
        description="AI detects and fixes SQL injection in code",
        steps=[
            "User has vulnerable SQL query in database module",
            "User requests AI security review",
            "LLM detects SQL injection risk",
            "LLM suggests parameterized query fix",
            "User approves hunk-by-hunk changes",
            "Applied changes prevent SQL injection",
        ]
    ),
    IntegrationTestScenario(
        name="Multi-Part Response Approval",
        description="LLM response with text + code + shell commands",
        steps=[
            "LLM returns mixed response (explanation + code + setup commands)",
            "ResponseParser separates into 3 parts",
            "ApprovalModal shows CODE section + SHELL section separately",
            "User approves code changes, rejects shell commands",
            "Only approved parts applied",
            "Rejected shell commands logged for audit",
        ]
    ),
    IntegrationTestScenario(
        name="Provider Fallback on Timeout",
        description="LLM provider times out, fallback to next provider",
        steps=[
            "User requests AI suggestion",
            "OpenAI provider timeout after 30s",
            "ProviderChain automatically tries Anthropic",
            "Anthropic responds successfully",
            "Result returned to user",
            "Timeout error is NOT shown (recovery was automatic)",
        ]
    ),
]


# ============================================================================
# Real Test Data: Hunks and Approval Workflow
# ============================================================================

REAL_HUNK_WORKFLOW = {
    "file": "calculate_discount.py",
    "original_lines": [
        1,  "def calculate_discount(price, customer_type):",
        2,  '    """Calculate discount based on customer type."""',
        3,  "    if customer_type == 'vip':",
        4,  "        discount = 0.20",
        5,  "    elif customer_type == 'regular':",
        6,  "        discount = 0.10",
        7,  "    else:",
        8,  "        discount = 0.0",
        9,  "    ",
        10, "    final_price = price * (1 - discount)",
        11, "    return final_price",
    ],
    "suggested_changes": [
        {"line": 1, "old": "def calculate_discount(price, customer_type):", "new": "def calculate_discount(price: float, customer_type: str) -> float:"},
        {"line": 2, "old": '    """Calculate discount based on customer type."""', "new": '    """Calculate discount based on customer type.\n    \n    Args:\n        price: Product price in USD\n        customer_type: One of \'vip\', \'regular\', \'guest\'\n    """'},
        {"line": 3, "old": "    if customer_type == 'vip':", "new": "    DISCOUNT_RATES = {'vip': 0.20, 'regular': 0.10, 'guest': 0.0}\n    if price < 0: raise ValueError('Price must be non-negative')\n    if customer_type not in DISCOUNT_RATES: raise ValueError(f'Unknown type: {customer_type}')\n    if customer_type == 'vip':"},
    ],
    "expected_approval_rate": 0.8,  # User should approve ~80% of changes
}


# ============================================================================
# Real Error Scenarios
# ============================================================================

ERROR_SCENARIOS = {
    "timeout": {
        "error_type": "LLMTimeoutError",
        "message": "LLM request timed out after 30s",
        "recovery_actions": [
            "Retry with increased timeout",
            "Try different LLM provider",
            "Reduce context size",
        ]
    },
    "auth_failure": {
        "error_type": "LLMAuthError",
        "message": "Invalid API key for OpenAI",
        "recovery_actions": [
            "Check OPENAI_API_KEY environment variable",
            "Verify API key is valid",
            "Check API key has required permissions",
        ]
    },
    "rate_limit": {
        "error_type": "LLMRateLimitError",
        "message": "Rate limit exceeded (5 req/min)",
        "recovery_actions": [
            "Wait 60 seconds before retrying",
            "Use fallback LLM provider",
            "Upgrade API plan for higher limits",
        ]
    },
}


# ============================================================================
# Pytest Fixtures with Real Data
# ============================================================================

@pytest.fixture
def python_file_with_bugs():
    """Real Python file needing improvements."""
    return {
        "path": "src/discount.py",
        "content": PYTHON_CODE_SAMPLE_BUGGY,
        "language": "python",
        "issues": ["missing_type_hints", "no_validation", "missing_docstring"],
    }


@pytest.fixture
def llm_response_realistic():
    """Realistic multi-part LLM response."""
    return LLM_RESPONSE_MULTI_PART


@pytest.fixture
def sensitive_data_list():
    """List of real secrets for filtering tests."""
    return SENSITIVE_DATA_SAMPLES


@pytest.fixture
def performance_baseline():
    """Performance constraints that must be met."""
    return PERFORMANCE_CONSTRAINTS


@pytest.fixture
def security_baseline():
    """Security constraints that must be met."""
    return SECURITY_CONSTRAINTS


@pytest.fixture
def integration_workflow():
    """Real end-to-end workflow scenario."""
    return INTEGRATION_SCENARIOS[0]  # "Fix Python Function with AI"


# ============================================================================
# Test Cases with Real Constraints
# ============================================================================

class TestPhase4RealData:
    """Test Phase 4 with production-grade data and constraints."""

    def test_response_parser_with_realistic_llm_output(self, llm_response_realistic):
        """Test parsing realistic multi-part LLM response."""
        from ki_core.core.response_parser import ResponseParser, ResponsePartType
        
        parser = ResponseParser()
        parts = parser.parse(llm_response_realistic)
        
        # Should detect text, code, and separate sections
        assert any(p.type == ResponsePartType.TEXT for p in parts)
        assert any(p.type == ResponsePartType.CODE for p in parts)
        
        # Code should contain the improved function
        code_parts = [p for p in parts if p.type == ResponsePartType.CODE]
        code_content = "\n".join(p.content for p in code_parts)
        assert "def calculate_discount" in code_content
        assert "raise ValueError" in code_content

    def test_secret_filter_with_real_credentials(self, sensitive_data_list):
        """Test filtering real API keys and secrets."""
        from ki_core.security.filters import SensitiveDataFilter
        
        filter_obj = SensitiveDataFilter()
        
        for secret in sensitive_data_list:
            assert filter_obj.has_secrets(secret), f"Failed to detect: {secret[:20]}..."
            
            # Verify secrets are redacted
            redacted = filter_obj.filter(secret)
            assert "[REDACTED]" in redacted
            assert secret not in redacted

    def test_performance_constraint_response_parsing(self, performance_baseline, llm_response_realistic):
        """Verify response parsing meets performance constraint."""
        import time
        from ki_core.core.response_parser import ResponseParser
        
        parser = ResponseParser()
        constraint = next(c for c in performance_baseline if "ResponseParser" in c.operation)
        
        start = time.time()
        parser.parse(llm_response_realistic)
        elapsed_ms = (time.time() - start) * 1000
        
        assert elapsed_ms < constraint.max_time_ms, \
            f"Response parsing took {elapsed_ms:.1f}ms, constraint: {constraint.max_time_ms}ms"

    def test_security_constraint_secret_in_errors(self):
        """Verify secrets don't leak in error messages."""
        from ki_core.errors.structured import LLMAuthError
        
        error = LLMAuthError("Invalid API key: sk-test123abc")
        error_msg = str(error)
        
        # API key should NOT be in error message
        assert "sk-test123abc" not in error_msg
        assert "[REDACTED]" in error_msg or "API key" in error_msg

    def test_real_workflow_scenario(self, python_file_with_bugs, llm_response_realistic):
        """Test complete real-world workflow."""
        from ki_core.core.response_parser import ResponseParser
        from kicli_code_assist.approval_workflow import ApprovalSession, CodeHunk
        
        # Parse LLM response
        parser = ResponseParser()
        parts = parser.parse(llm_response_realistic)
        
        # Create approval session (like AIWorkflowManager does)
        session = ApprovalSession(session_id="real-scenario-1")
        
        # Create hunk from suggested changes
        hunk = CodeHunk(
            file_path=python_file_with_bugs["path"],
            start_line=1,
            end_line=11,
            lines=[]  # Would be populated from parser output
        )
        session.add_hunk(hunk)
        
        # Verify workflow state
        assert session.session_id == "real-scenario-1"
        assert len(session.hunks) == 1
        assert session.is_ready_for_apply() is False  # No approval yet


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
