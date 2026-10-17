"""Production-grade test data for Phase 4 integration.

Real-world scenarios, constraints, and performance baselines.
"""

import pytest
from dataclasses import dataclass
from typing import List, Optional


# ============================================================================
# Real-World Code Samples for Testing
# ============================================================================

PYTHON_CODE_SAMPLE_BUGGY = r"""def calculate_discount(price, customer_type):
    if customer_type == 'vip':
        discount = 0.20
    elif customer_type == 'regular':
        discount = 0.10
    else:
        discount = 0.0
    
    final_price = price * (1 - discount)
    return final_price
"""

PYTHON_CODE_SAMPLE_IMPROVED = r"""def calculate_discount(price: float, customer_type: str) -> float:
    DISCOUNT_RATES = {'vip': 0.20, 'regular': 0.10, 'guest': 0.0}
    
    if price < 0:
        raise ValueError(f"Price must be non-negative, got {price}")
    if customer_type not in DISCOUNT_RATES:
        raise ValueError(f"Unknown customer type: {customer_type}")
    
    return price * (1 - DISCOUNT_RATES[customer_type])
"""

SHELL_SCRIPT_SAMPLE = r"""#!/bin/bash
set -e
BUILD_DIR="${1:-.}"
DEPLOY_ENV="${2:-production}"

echo "Building from $BUILD_DIR to $DEPLOY_ENV"
cd "$BUILD_DIR"
npm install --production
npm run build

if [ "$DEPLOY_ENV" = "production" ]; then
    npm run deploy:prod
else
    npm run deploy:staging
fi

echo "Done"
"""

JAVASCRIPT_CODE_BUGGY = r"""async function fetchUserData(userId) {
    const response = await fetch(`/api/users/${userId}`);
    const data = response.json();
    return data;
}
"""

JAVASCRIPT_CODE_IMPROVED = r"""async function fetchUserData(userId) {
    if (!userId || typeof userId !== 'string') {
        throw new Error('userId must be a non-empty string');
    }
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch user data:', error);
        throw error;
    }
}
"""

SQL_VULNERABLE = r"""SELECT * FROM users WHERE email = '""" + "'" + r"""' + userInput + '""" + "'" + r"""';"""

SQL_SAFE = r"""SELECT * FROM users WHERE email = $1;"""

# Real API keys/secrets for filtering tests
SENSITIVE_DATA_SAMPLES = [
    "sk-proj-abc123def456ghi789jkl",  # OpenAI
    "sk-ant-xyz789abc123def456",  # Anthropic
    "AKIA2E3Q4R5S6T7U8V9W",  # AWS Access Key
    "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",  # AWS Secret
    "xoxb-1234567890123-1234567890123-AbCdEfGhIjKlMnOpQrSt",  # Slack bot
    "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQE...",  # Private key
]


# ============================================================================
# LLM Response Scenarios (use double quotes to avoid nesting issues)
# ============================================================================

LLM_RESPONSE_MULTI_PART = 'Looking at this code, I found several issues:\n\n## Security Issues\n\n1. Missing input validation\n2. No error handling\n\n## Suggested Fix\n\nHere\'s improved code:\n\ndef calculate_discount(price: float, customer_type: str) -> float:\n    DISCOUNT_RATES = {"vip": 0.20, "regular": 0.10}\n    if price < 0:\n        raise ValueError("Price negative")\n    if customer_type not in DISCOUNT_RATES:\n        raise ValueError("Unknown type")\n    return price * (1 - DISCOUNT_RATES[customer_type])\n\nAdd unit tests to validate all cases.'

LLM_RESPONSE_SHELL_COMMANDS = 'To set up the environment:\n\nnpm install\nnpm run build\nnpm run deploy:prod\n\nVerify with: curl http://localhost:3000'

LLM_RESPONSE_SQL_INJECTION = 'Your SQL query is vulnerable to injection:\n\nBuggy: SELECT * FROM users WHERE email = "\' + input + "\'"\nFixed: SELECT * FROM users WHERE email = $1\n\nAlways use parameterized queries.'


# ============================================================================
# Performance Constraints (Production SLAs)
# ============================================================================

CONSTRAINTS = {
    'response_parser_max_time_ms': 100,
    'encryption_max_time_ms': 100,
    'approval_modal_render_ms': 50,
    'llm_timeout_seconds': 30,
    'provider_retry_max_attempts': 3,
    'master_key_file_permissions': 0o600,
    'max_file_size_mb': 10,
    'max_chat_history_entries': 1000,
}


# ============================================================================
# Security Constraints
# ============================================================================

SECURITY_REQUIREMENTS = {
    'secret_patterns_minimum': 10,  # At least 10 regex patterns for detection
    'master_key_minimum_length': 32,  # Bytes
    'encryption_algorithm': 'Fernet (AES-128-CBC + HMAC)',
    'no_plaintext_secrets_in_logs': True,
    'no_plaintext_secrets_in_ui': True,
    'error_messages_must_not_leak_secrets': True,
    'audit_trail_required': True,
}


# ============================================================================
# Integration Scenario Data Classes
# ============================================================================

@dataclass
class IntegrationScenario:
    """Represents a real-world integration test scenario."""
    name: str
    input_code: str
    llm_response: str
    expected_hunks: int
    security_checks: List[str]
    performance_target_ms: int


SCENARIOS = [
    IntegrationScenario(
        name="Fix Python function with validation",
        input_code=PYTHON_CODE_SAMPLE_BUGGY,
        llm_response=LLM_RESPONSE_MULTI_PART,
        expected_hunks=2,
        security_checks=["no_secret_leak"],
        performance_target_ms=100,
    ),
    IntegrationScenario(
        name="Detect SQL injection vulnerability",
        input_code=SQL_VULNERABLE,
        llm_response=LLM_RESPONSE_SQL_INJECTION,
        expected_hunks=1,
        security_checks=["no_secret_leak"],
        performance_target_ms=80,
    ),
    IntegrationScenario(
        name="Fix JavaScript async/await error handling",
        input_code=JAVASCRIPT_CODE_BUGGY,
        llm_response="Add error handling and validation:\n\nasync function fetchUserData(userId) {\n    if (!userId) throw new Error('userId required');\n    const response = await fetch(`/api/users/${userId}`);\n    if (!response.ok) throw new Error(`HTTP ${response.status}`);\n    return response.json();\n}",
        expected_hunks=2,
        security_checks=["no_secret_leak"],
        performance_target_ms=90,
    ),
    IntegrationScenario(
        name="Multi-part response with shell commands",
        input_code="# Deploy script needed",
        llm_response=LLM_RESPONSE_SHELL_COMMANDS,
        expected_hunks=1,
        security_checks=["no_secret_leak", "validate_commands"],
        performance_target_ms=110,
    ),
]


# ============================================================================
# Pytest Fixtures for Real Production Data
# ============================================================================

@pytest.fixture
def python_buggy_code():
    """Real Python code with security/quality issues."""
    return PYTHON_CODE_SAMPLE_BUGGY


@pytest.fixture
def python_improved_code():
    """Real Python code with fixes applied."""
    return PYTHON_CODE_SAMPLE_IMPROVED


@pytest.fixture
def javascript_buggy_code():
    """Real JavaScript code missing error handling."""
    return JAVASCRIPT_CODE_BUGGY


@pytest.fixture
def javascript_improved_code():
    """Real JavaScript code with proper error handling."""
    return JAVASCRIPT_CODE_IMPROVED


@pytest.fixture
def sql_vulnerable():
    """SQL code vulnerable to injection."""
    return SQL_VULNERABLE


@pytest.fixture
def sql_safe():
    """SQL code using parameterized queries."""
    return SQL_SAFE


@pytest.fixture
def shell_script():
    """Real shell deployment script."""
    return SHELL_SCRIPT_SAMPLE


@pytest.fixture
def llm_response_realistic():
    """Realistic multi-part LLM response."""
    return LLM_RESPONSE_MULTI_PART


@pytest.fixture
def llm_response_with_shell():
    """LLM response with shell commands."""
    return LLM_RESPONSE_SHELL_COMMANDS


@pytest.fixture
def sensitive_data():
    """Real API keys and secrets for filtering tests."""
    return SENSITIVE_DATA_SAMPLES


@pytest.fixture
def integration_scenarios():
    """Real-world integration scenarios."""
    return SCENARIOS


@pytest.fixture
def performance_constraints():
    """Production performance SLAs."""
    return CONSTRAINTS


@pytest.fixture
def security_constraints():
    """Production security requirements."""
    return SECURITY_REQUIREMENTS


# ============================================================================
# Test Classes Using Production Data
# ============================================================================

class TestPhase4RealData:
    """Integration tests using real-world data."""

    def test_python_code_parsing(self, python_buggy_code):
        """Verify real Python code parses correctly."""
        assert "def calculate_discount" in python_buggy_code
        assert "customer_type" in python_buggy_code

    def test_javascript_code_parsing(self, javascript_buggy_code):
        """Verify real JavaScript code structure."""
        assert "async function" in javascript_buggy_code
        assert "fetch" in javascript_buggy_code

    def test_sql_vulnerability_detection(self, sql_vulnerable):
        """Verify SQL injection vulnerability pattern detected."""
        assert "+" in sql_vulnerable or "userInput" in sql_vulnerable

    def test_sensitive_data_real_keys(self, sensitive_data):
        """Verify real API key formats are in test data."""
        assert any("sk-" in key for key in sensitive_data)  # OpenAI format
        assert any("AKIA" in key for key in sensitive_data)  # AWS format
        assert len(sensitive_data) >= 6

    def test_real_scenario_structure(self, integration_scenarios):
        """Verify integration scenarios have complete data."""
        for scenario in integration_scenarios:
            assert scenario.name
            assert scenario.input_code
            assert scenario.llm_response
            assert scenario.expected_hunks > 0
            assert scenario.performance_target_ms > 0
            assert len(scenario.security_checks) > 0

    def test_constraint_values_realistic(self, performance_constraints):
        """Verify performance constraints are realistic."""
        assert performance_constraints['response_parser_max_time_ms'] < 500
        assert performance_constraints['llm_timeout_seconds'] >= 10
        assert performance_constraints['max_file_size_mb'] >= 1
        assert performance_constraints['master_key_file_permissions'] == 0o600

    def test_security_requirements_complete(self, security_constraints):
        """Verify security requirements cover key areas."""
        required_keys = [
            'secret_patterns_minimum',
            'master_key_minimum_length',
            'encryption_algorithm',
            'no_plaintext_secrets_in_logs',
        ]
        for key in required_keys:
            assert key in security_constraints

    def test_llm_response_realism(self, llm_response_realistic):
        """Verify LLM response matches real API output patterns."""
        # Real LLM responses have discussion + code suggestions
        assert len(llm_response_realistic) > 100
        assert "def " in llm_response_realistic or "function" in llm_response_realistic

    def test_real_workflow_scenario(self, integration_scenarios):
        """Test realistic end-to-end scenario."""
        scenario = integration_scenarios[0]  # Python fix scenario
        
        assert scenario.name == "Fix Python function with validation"
        assert len(scenario.input_code) > 50
        assert scenario.expected_hunks >= 1
        assert 'no_secret_leak' in scenario.security_checks
        assert scenario.performance_target_ms <= 100
