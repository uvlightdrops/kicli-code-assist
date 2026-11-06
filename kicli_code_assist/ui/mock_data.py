"""Mock data for testing Agent Response and Chunks display."""

# Mock Response - ~10 sentences (realistic analysis output)
MOCK_RESPONSES = {
    "explain": """This module implements the core configuration management system for the application. The ConfigManager class is responsible for loading, validating, and merging configuration from multiple sources including environment variables, YAML files, and runtime parameters. It supports hierarchical configuration with environment-specific overrides and provides a unified interface for accessing configuration values throughout the application. The system implements a smart merge strategy that handles conflicts between sources and maintains backward compatibility with legacy configuration formats. Configuration validation is performed at load time to ensure type safety and required fields are present before the application starts. The module also provides facilities for logging configuration changes and monitoring for updates in watch mode. Performance is optimized through lazy loading of rarely-used configuration sections and caching of computed values. Error handling includes detailed error messages to help developers debug configuration issues quickly. The implementation has been battle-tested across multiple deployment environments including development, staging, and production. Integration with the dependency injection system allows configuration to be injected into service layers cleanly and testably.""",
    
    "metrics": """The analyzed file has a maintainability index of 7.2 out of 10, indicating moderate complexity. Cyclomatic complexity across functions ranges from 2 to 8, with the largest function having 8 branches which exceeds the recommended threshold of 5. The file contains 320 lines of code with good separation of concerns across 7 functions and 1 class. Test coverage is currently at 73%, missing coverage for error handling paths and edge cases. Code duplication is minimal at 1.2% with only a few repeated utility functions. The average function length is 45 lines, which is within acceptable bounds but some functions could be refactored into smaller components. Cognitive complexity analysis shows that the ConfigManager class has higher complexity than other classes due to nested conditionals in the merge logic. The code follows PEP 8 style guidelines consistently with appropriate docstrings for public methods. Performance profiling indicates that configuration loading takes approximately 12ms for typical deployments. Documentation is comprehensive with examples provided for common use cases.""",
    
    "refactor": """Several refactoring opportunities have been identified to improve code quality and maintainability. The merge_config function should be extracted into a separate ConfigMerger class to reduce complexity and enable better testing. Error handling could be improved by using custom exception types instead of generic exceptions, making error recovery more robust. The validation logic is currently scattered across multiple methods and should be consolidated into a ConfigValidator class for consistency. Some helper functions are candidates for moving into a utilities module to reduce the size of the main class. The watch mode implementation could benefit from using a file system watcher library instead of polling. Test coverage gaps in error paths should be addressed by adding integration tests for failure scenarios. The ConfigManager could implement a factory pattern for creating configuration instances with different strategies. Performance can be improved by implementing lazy loading for large configuration sections. Documentation could include a diagram of the configuration merge process to clarify the precedence rules.""",
    
    "dependencies": """This module depends on 5 internal modules and 8 external packages. Internal dependencies include utils.logging for logger setup, core.errors for exception types, security.filters for sensitive data filtering, adapters.openai for LLM integration, and schema.validator for YAML schema validation. External dependencies are yaml, pydantic, python-dotenv, loguru, typing-extensions, pathlib2, attrs, and dacite. Reverse dependencies show that 12 modules throughout the codebase import from this configuration system including the server, all agent modules, and CLI utilities. Changes to the ConfigManager interface would require updates to multiple integration points across the application. The circular dependency risk is low due to careful interface design. Test modules have direct dependencies on this module for test fixture setup. Documentation should be updated whenever the configuration schema changes. Three modules have optional imports that gracefully degrade if certain packages are unavailable.""",
}

# Mock Chunks - ~10 items (thinking/observation stream)
MOCK_CHUNKS = {
    "explain": [
        ("observation", "The file starts with import statements for logging, pathlib, and typing modules"),
        ("observation", "Found a ConfigManager class with __init__, load, validate, and merge methods"),
        ("observation", "The class has 320 lines of code spanning 45 lines per method on average"),
        ("issue", "The merge method contains nested if-elif blocks with cyclomatic complexity of 8"),
        ("solution", "Extract merge logic into separate ConfigMerger class to reduce complexity"),
        ("observation", "Docstrings are present for public methods but some parameters lack type hints"),
        ("issue", "Error handling uses generic Exception instead of custom exception types"),
        ("solution", "Define ConfigError, ValidationError, and MergeError for better error handling"),
        ("impact", "These changes would improve maintainability index from 7.2 to estimated 8.1"),
        ("info", "File follows PEP 8 style guidelines consistently"),
    ],
    
    "metrics": [
        ("observation", "Analyzed 320 lines of code across 7 functions and 1 class"),
        ("observation", "Cyclomatic complexity: min=2, max=8, avg=4.6"),
        ("issue", "Function at line 142 has complexity 8, exceeds recommended threshold of 5"),
        ("observation", "Test coverage: 73% (good) but missing error handling paths"),
        ("issue", "ConfigValidator.validate method has no test coverage for edge cases"),
        ("solution", "Add integration tests for invalid YAML, missing files, and corrupt data"),
        ("observation", "Code duplication is minimal at 1.2%"),
        ("observation", "Average function length: 45 lines (acceptable range)"),
        ("impact", "Addressing complexity and coverage would bring maintainability to 8.5+"),
        ("info", "Performance baseline: configuration load time 12ms for typical deployments"),
    ],
    
    "refactor": [
        ("observation", "Identified 6 refactoring opportunities with high confidence"),
        ("solution", "Extract ConfigMerger class: move merge_config, handle_conflicts methods"),
        ("solution", "Create ConfigValidator class: consolidate all validation logic"),
        ("solution", "Define custom exception hierarchy: ConfigError, ValidationError, MergeError"),
        ("issue", "Watch mode uses polling instead of file system watcher (inefficient)"),
        ("solution", "Integrate watchdog library for efficient file system monitoring"),
        ("observation", "Test coverage gaps in error paths: 5 functions lack error scenario testing"),
        ("solution", "Add integration tests for file not found, permission denied, YAML parse errors"),
        ("impact", "After refactoring: complexity 5.2, coverage 92%, maintainability 8.8"),
        ("info", "Estimated effort: 8-12 hours, provides long-term maintainability gains"),
    ],
}

def get_mock_response(agent_type: str) -> str:
    """Get mock response for agent type."""
    return MOCK_RESPONSES.get(agent_type, "No mock data available for this agent type.")

def get_mock_chunks(agent_type: str) -> list:
    """Get mock chunks for agent type.
    
    Returns:
        List of (type, content) tuples
    """
    return MOCK_CHUNKS.get(agent_type, [])
