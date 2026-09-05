"""Prompt management - manager class for handling prompt roles and templates."""

from typing import Dict, Optional, List, Any
from .models import (
    PromptRole,
    CustomTemplate,
    LanguageLearningConfig,
    LanguageLearningLevel,
    PromptsConfig,
)


class PromptManager:
    """Manage prompt roles, templates, and language learning settings."""
    
    # Built-in default roles
    DEFAULT_ROLES: Dict[str, Dict[str, str]] = {
        "developer": {
            "name": "Developer",
            "description": "Technical assistance for software development",
            "system_prompt": (
                "You are an expert software developer with deep knowledge of:\n"
                "- Multiple programming languages and frameworks\n"
                "- Software architecture and design patterns\n"
                "- Best practices and clean code principles\n"
                "- Security and performance optimization\n\n"
                "When helping with code:\n"
                "- Provide clear explanations\n"
                "- Suggest improvements when appropriate\n"
                "- Ask clarifying questions if needed\n"
                "- Include examples and best practices"
            ),
        },
        "tutor": {
            "name": "Tutor",
            "description": "Educational mode with explanations",
            "system_prompt": (
                "You are a patient and encouraging educator who:\n"
                "- Explains concepts clearly with examples\n"
                "- Adapts to different learning levels\n"
                "- Asks guiding questions to promote understanding\n"
                "- Celebrates learning progress\n"
                "- Never gives direct answers without guidance\n\n"
                "Your goal is to help people learn, not just get answers."
            ),
        },
        "translator": {
            "name": "Translator",
            "description": "Translation and language support",
            "system_prompt": (
                "You are a professional translator with expertise in:\n"
                "- Multiple languages and dialects\n"
                "- Cultural and contextual meanings\n"
                "- Formal and informal communication styles\n"
                "- Technical and specialized terminology\n\n"
                "When translating:\n"
                "- Preserve meaning and nuance\n"
                "- Adapt to context and audience\n"
                "- Provide alternatives when helpful\n"
                "- Explain cultural references when needed"
            ),
        },
        "language_learning": {
            "name": "Language Learning",
            "description": "Learn languages in target language",
            "system_prompt": (
                "You are a language learning companion who:\n"
                "- Responds primarily in the target language\n"
                "- Corrects mistakes gently and constructively\n"
                "- Provides translations on request (tag with [EN]: )\n"
                "- Uses vocabulary appropriate to the student's level\n"
                "- Encourages practice through conversation"
            ),
        },
        "code_reviewer": {
            "name": "Code Reviewer",
            "description": "Expert code review and improvement",
            "system_prompt": (
                "You are a senior code reviewer who:\n"
                "- Analyzes code for quality, security, and performance\n"
                "- Provides constructive, actionable feedback\n"
                "- Explains the 'why' behind suggestions\n"
                "- Considers maintainability and readability\n"
                "- Follows industry best practices\n\n"
                "Review focus areas:\n"
                "1. Code quality and style\n"
                "2. Security vulnerabilities\n"
                "3. Performance implications\n"
                "4. Maintainability and clarity\n"
                "5. Test coverage"
            ),
        },
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize PromptManager from config dictionary.
        
        Args:
            config: Configuration dict with optional 'prompts' section
        """
        self.config = config
        prompts_data = config.get('prompts', {})
        
        # Load or create PromptsConfig
        self.prompts_config = PromptsConfig.from_dict(prompts_data)
        
        # Initialize default roles if not present
        self._init_default_roles()
    
    def _init_default_roles(self) -> None:
        """Initialize default roles if they don't exist."""
        for role_id, role_data in self.DEFAULT_ROLES.items():
            if role_id not in self.prompts_config.roles:
                role = PromptRole(
                    id=role_id,
                    name=role_data['name'],
                    description=role_data['description'],
                    system_prompt=role_data['system_prompt'],
                )
                self.prompts_config.roles[role_id] = role
    
    # --- Active Role Management ---
    
    def get_active_role(self) -> Optional[PromptRole]:
        """Get the currently active role."""
        return self.prompts_config.get_role(self.prompts_config.active_role)
    
    def set_active_role(self, role_id: str) -> bool:
        """Set the active role.
        
        Args:
            role_id: ID of the role to activate
            
        Returns:
            True if successful, False if role not found
        """
        if role_id not in self.prompts_config.roles:
            return False
        
        self.prompts_config.active_role = role_id
        return True
    
    def get_active_role_prompt(self) -> Optional[str]:
        """Get the system prompt of the active role."""
        role = self.get_active_role()
        return role.system_prompt if role else None
    
    # --- Role Management ---
    
    def list_roles(self) -> Dict[str, PromptRole]:
        """Get all available roles."""
        return self.prompts_config.roles
    
    def get_role(self, role_id: str) -> Optional[PromptRole]:
        """Get a specific role by ID."""
        return self.prompts_config.get_role(role_id)
    
    def role_exists(self, role_id: str) -> bool:
        """Check if a role exists."""
        return role_id in self.prompts_config.roles
    
    def list_enabled_roles(self) -> Dict[str, PromptRole]:
        """Get all enabled roles."""
        return {
            rid: role for rid, role in self.prompts_config.roles.items()
            if role.enabled
        }
    
    # --- Custom Template Management ---
    
    def create_template(self, template: CustomTemplate) -> bool:
        """Create a new custom template.
        
        Args:
            template: CustomTemplate to create
            
        Returns:
            True if successful, False if template ID already exists
        """
        if self.prompts_config.get_template(template.id):
            return False
        
        self.prompts_config.custom_templates.append(template)
        return True
    
    def update_template(self, template: CustomTemplate) -> bool:
        """Update an existing custom template.
        
        Args:
            template: CustomTemplate with updated data
            
        Returns:
            True if successful, False if template not found
        """
        existing = self.prompts_config.get_template(template.id)
        if not existing:
            return False
        
        # Update the existing template in-place
        idx = self.prompts_config.custom_templates.index(existing)
        template.modified_at = template.modified_at  # Keep creation time
        self.prompts_config.custom_templates[idx] = template
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template.
        
        Args:
            template_id: ID of template to delete
            
        Returns:
            True if successful, False if template not found
        """
        template = self.prompts_config.get_template(template_id)
        if not template:
            return False
        
        self.prompts_config.custom_templates.remove(template)
        return True
    
    def list_templates(self) -> List[CustomTemplate]:
        """Get all custom templates."""
        return self.prompts_config.custom_templates
    
    def get_template(self, template_id: str) -> Optional[CustomTemplate]:
        """Get a specific custom template."""
        return self.prompts_config.get_template(template_id)
    
    def search_templates(self, query: str) -> List[CustomTemplate]:
        """Search templates by name, description, or tags.
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of matching templates
        """
        query_lower = query.lower()
        results = []
        
        for template in self.prompts_config.custom_templates:
            if (query_lower in template.name.lower() or
                query_lower in template.description.lower() or
                any(query_lower in tag.lower() for tag in template.tags)):
                results.append(template)
        
        return results
    
    # --- Favorites Management ---
    
    def add_favorite(self, identifier: str) -> bool:
        """Add a role or template to favorites.
        
        Args:
            identifier: Role ID or template ID
            
        Returns:
            True if successful
        """
        if identifier not in self.prompts_config.favorites:
            self.prompts_config.favorites.append(identifier)
            return True
        return False
    
    def remove_favorite(self, identifier: str) -> bool:
        """Remove a role or template from favorites.
        
        Args:
            identifier: Role ID or template ID
            
        Returns:
            True if successful
        """
        if identifier in self.prompts_config.favorites:
            self.prompts_config.favorites.remove(identifier)
            return True
        return False
    
    def get_favorites(self) -> List[str]:
        """Get list of favorite IDs."""
        return self.prompts_config.favorites
    
    def is_favorite(self, identifier: str) -> bool:
        """Check if an identifier is favorited."""
        return identifier in self.prompts_config.favorites
    
    # --- Language Learning ---
    
    def enable_language_learning(self, target_language: str, level: str = "beginner") -> bool:
        """Enable language learning mode.
        
        Args:
            target_language: Language to learn
            level: Difficulty level (beginner, intermediate, advanced)
            
        Returns:
            True if successful
        """
        try:
            ll_level = LanguageLearningLevel(level)
        except ValueError:
            return False
        
        self.prompts_config.language_learning.enabled = True
        self.prompts_config.language_learning.target_language = target_language
        self.prompts_config.language_learning.level = ll_level
        return True
    
    def disable_language_learning(self) -> None:
        """Disable language learning mode."""
        self.prompts_config.language_learning.enabled = False
    
    def is_language_learning_enabled(self) -> bool:
        """Check if language learning mode is enabled."""
        return self.prompts_config.language_learning.enabled
    
    def get_language_learning_prompt(self) -> Optional[str]:
        """Get the language learning system prompt injection.
        
        Returns:
            Prompt injection string or None if not enabled
        """
        if not self.is_language_learning_enabled():
            return None
        
        ll = self.prompts_config.language_learning
        level_desc = {
            LanguageLearningLevel.BEGINNER: "simple vocabulary and short sentences",
            LanguageLearningLevel.INTERMEDIATE: "natural pacing and some idioms",
            LanguageLearningLevel.ADVANCED: "native-like speed and advanced concepts",
        }
        
        level_text = level_desc.get(ll.level, "appropriate level")
        
        return (
            f"You are in Language Learning mode:\n"
            f"- Respond primarily in {ll.target_language}\n"
            f"- Use {level_text}\n"
            f"- Correct mistakes gently\n"
            f"- Provide translations on request (prefixed with [{ll.native_language}]: )"
        )
    
    def get_effective_system_prompt(self) -> str:
        """Get the effective system prompt (active role + LL if enabled).
        
        Returns:
            Combined system prompt string
        """
        base_prompt = self.get_active_role_prompt() or ""
        
        if self.is_language_learning_enabled():
            ll_prompt = self.get_language_learning_prompt()
            return f"{base_prompt}\n\n{ll_prompt}"
        
        return base_prompt
    
    # --- Config Export/Import ---
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to dictionary."""
        return self.prompts_config.to_dict()
    
    def to_config(self) -> Dict[str, Any]:
        """Export configuration in the format expected by config system."""
        return {'prompts': self.to_dict()}
