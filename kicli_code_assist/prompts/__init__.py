"""Prompt management module for KI CLI."""

from .models import (
    CustomTemplate,
    LanguageLearningConfig,
    LanguageLearningLevel,
    PromptRole as PromptRoleDataclass,
    PromptsConfig,
)
from .manager import PromptManager

# Import legacy classes for backward compatibility
import sys
from pathlib import Path
import importlib.util

# Load legacy prompts.py for backward compatibility
legacy_path = Path(__file__).parent.parent / "prompts.py"
if legacy_path.exists():
    spec = importlib.util.spec_from_file_location("_legacy_prompts", legacy_path)
    _legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_legacy)
    
    # Export legacy classes
    PromptRole = _legacy.PromptRole
    SystemPrompts = _legacy.SystemPrompts
    PromptTemplates = _legacy.PromptTemplates
else:
    # Fallback if legacy file doesn't exist
    PromptRole = None
    SystemPrompts = None
    PromptTemplates = None

__all__ = [
    # New classes
    "CustomTemplate",
    "LanguageLearningConfig",
    "LanguageLearningLevel",
    "PromptRoleDataclass",
    "PromptsConfig",
    "PromptManager",
    # Legacy classes (backward compatibility)
    "PromptRole",
    "SystemPrompts",
    "PromptTemplates",
]
