"""Prompt management models and data structures."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum


class LanguageLearningLevel(Enum):
    """Language learning difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class CustomTemplate:
    """User-defined prompt template."""
    id: str
    name: str
    system_prompt: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.modified_at is None:
            self.modified_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.modified_at:
            data['modified_at'] = self.modified_at.isoformat()
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CustomTemplate':
        """Create from dictionary (e.g., from YAML)."""
        # Convert ISO format strings back to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('modified_at'), str):
            data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        return CustomTemplate(**data)


@dataclass
class PromptRole:
    """Built-in or custom prompt role definition."""
    id: str
    name: str
    system_prompt: str
    description: str = ""
    enabled: bool = True
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(role_id: str, data: Dict[str, Any]) -> 'PromptRole':
        """Create from dictionary."""
        # Remove 'id' from data if it exists to avoid duplicate keyword argument
        data_copy = {k: v for k, v in data.items() if k != 'id'}
        return PromptRole(id=role_id, **data_copy)


@dataclass
class LanguageLearningConfig:
    """Language learning mode configuration."""
    enabled: bool = False
    target_language: str = ""
    native_language: str = "English"
    level: LanguageLearningLevel = LanguageLearningLevel.BEGINNER
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enabled': self.enabled,
            'target_language': self.target_language,
            'native_language': self.native_language,
            'level': self.level.value,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'LanguageLearningConfig':
        """Create from dictionary."""
        level = data.get('level', 'beginner')
        if isinstance(level, str):
            level = LanguageLearningLevel(level)
        return LanguageLearningConfig(
            enabled=data.get('enabled', False),
            target_language=data.get('target_language', ''),
            native_language=data.get('native_language', 'English'),
            level=level,
        )


@dataclass
class PromptsConfig:
    """Complete prompts configuration."""
    active_role: str = "developer"
    roles: Dict[str, PromptRole] = field(default_factory=dict)
    custom_templates: List[CustomTemplate] = field(default_factory=list)
    language_learning: LanguageLearningConfig = field(default_factory=LanguageLearningConfig)
    favorites: List[str] = field(default_factory=list)
    auto_save_custom: bool = True
    
    def get_role(self, role_id: str) -> Optional[PromptRole]:
        """Get a role by ID."""
        return self.roles.get(role_id)
    
    def get_template(self, template_id: str) -> Optional[CustomTemplate]:
        """Get a custom template by ID."""
        for template in self.custom_templates:
            if template.id == template_id:
                return template
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'active_role': self.active_role,
            'roles': {role_id: role.to_dict() for role_id, role in self.roles.items()},
            'custom_templates': [t.to_dict() for t in self.custom_templates],
            'language_learning': self.language_learning.to_dict(),
            'favorites': self.favorites,
            'auto_save_custom': self.auto_save_custom,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PromptsConfig':
        """Create from dictionary."""
        # Parse roles
        roles = {}
        for role_id, role_data in data.get('roles', {}).items():
            roles[role_id] = PromptRole.from_dict(role_id, role_data)
        
        # Parse custom templates
        custom_templates = [
            CustomTemplate.from_dict(template_data)
            for template_data in data.get('custom_templates', [])
        ]
        
        # Parse language learning config
        language_learning = LanguageLearningConfig.from_dict(
            data.get('language_learning', {})
        )
        
        return PromptsConfig(
            active_role=data.get('active_role', 'developer'),
            roles=roles,
            custom_templates=custom_templates,
            language_learning=language_learning,
            favorites=data.get('favorites', []),
            auto_save_custom=data.get('auto_save_custom', True),
        )
