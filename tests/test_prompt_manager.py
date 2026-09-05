"""Unit tests for prompt management system."""

import pytest
from datetime import datetime
from kicli_code_assist.prompts.models import (
    CustomTemplate,
    LanguageLearningConfig,
    LanguageLearningLevel,
    PromptRole,
    PromptsConfig,
)
from kicli_code_assist.prompts.manager import PromptManager


# --- CustomTemplate Tests ---


class TestCustomTemplate:
    """Test CustomTemplate model."""
    
    def test_create_template(self):
        """Test basic template creation."""
        template = CustomTemplate(
            id="test-template",
            name="Test Template",
            system_prompt="Test prompt",
        )
        assert template.id == "test-template"
        assert template.name == "Test Template"
        assert template.system_prompt == "Test prompt"
        assert template.description == ""
        assert template.tags == []
        assert template.created_at is not None
    
    def test_template_with_tags(self):
        """Test template with tags."""
        template = CustomTemplate(
            id="tagged",
            name="Tagged Template",
            system_prompt="Prompt",
            tags=["python", "debugging"],
        )
        assert template.tags == ["python", "debugging"]
    
    def test_template_to_dict(self):
        """Test template serialization."""
        template = CustomTemplate(
            id="test",
            name="Test",
            system_prompt="Prompt",
            tags=["tag1"],
        )
        data = template.to_dict()
        assert data['id'] == "test"
        assert data['name'] == "Test"
        assert 'created_at' in data
        assert isinstance(data['created_at'], str)
    
    def test_template_from_dict(self):
        """Test template deserialization."""
        data = {
            'id': 'test',
            'name': 'Test',
            'system_prompt': 'Prompt',
            'description': 'A test template',
            'tags': ['tag1', 'tag2'],
            'created_at': '2024-01-01T00:00:00',
            'modified_at': '2024-01-02T00:00:00',
        }
        template = CustomTemplate.from_dict(data)
        assert template.id == 'test'
        assert template.name == 'Test'
        assert isinstance(template.created_at, datetime)
        assert template.tags == ['tag1', 'tag2']


# --- LanguageLearningConfig Tests ---


class TestLanguageLearningConfig:
    """Test LanguageLearningConfig model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = LanguageLearningConfig()
        assert config.enabled is False
        assert config.target_language == ""
        assert config.native_language == "English"
        assert config.level == LanguageLearningLevel.BEGINNER
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LanguageLearningConfig(
            enabled=True,
            target_language="Deutsch",
            native_language="English",
            level=LanguageLearningLevel.INTERMEDIATE,
        )
        assert config.enabled is True
        assert config.target_language == "Deutsch"
        assert config.level == LanguageLearningLevel.INTERMEDIATE
    
    def test_language_learning_to_dict(self):
        """Test serialization."""
        config = LanguageLearningConfig(
            enabled=True,
            target_language="Español",
            level=LanguageLearningLevel.ADVANCED,
        )
        data = config.to_dict()
        assert data['enabled'] is True
        assert data['target_language'] == "Español"
        assert data['level'] == "advanced"
    
    def test_language_learning_from_dict(self):
        """Test deserialization."""
        data = {
            'enabled': True,
            'target_language': 'Français',
            'native_language': 'English',
            'level': 'intermediate',
        }
        config = LanguageLearningConfig.from_dict(data)
        assert config.enabled is True
        assert config.target_language == 'Français'
        assert config.level == LanguageLearningLevel.INTERMEDIATE


# --- PromptRole Tests ---


class TestPromptRole:
    """Test PromptRole model."""
    
    def test_create_role(self):
        """Test role creation."""
        role = PromptRole(
            id="test-role",
            name="Test Role",
            system_prompt="Test prompt",
        )
        assert role.id == "test-role"
        assert role.name == "Test Role"
        assert role.enabled is True
        assert role.version == "1.0"
    
    def test_role_to_dict(self):
        """Test role serialization."""
        role = PromptRole(
            id="test",
            name="Test",
            system_prompt="Prompt",
            description="Test role",
            tags=["custom"],
        )
        data = role.to_dict()
        assert data['id'] == "test"
        assert data['enabled'] is True
        assert data['tags'] == ["custom"]
    
    def test_role_from_dict(self):
        """Test role deserialization."""
        data = {
            'name': 'Test Role',
            'system_prompt': 'Prompt',
            'description': 'A test role',
            'enabled': False,
            'version': '2.0',
        }
        role = PromptRole.from_dict('test-id', data)
        assert role.id == 'test-id'
        assert role.name == 'Test Role'
        assert role.enabled is False
        assert role.version == '2.0'


# --- PromptsConfig Tests ---


class TestPromptsConfig:
    """Test PromptsConfig model."""
    
    def test_create_config(self):
        """Test config creation."""
        config = PromptsConfig()
        assert config.active_role == "developer"
        assert config.roles == {}
        assert config.custom_templates == []
        assert config.auto_save_custom is True
    
    def test_get_role(self):
        """Test getting role."""
        role = PromptRole(id="test", name="Test", system_prompt="Prompt")
        config = PromptsConfig(roles={"test": role})
        assert config.get_role("test") == role
        assert config.get_role("nonexistent") is None
    
    def test_get_template(self):
        """Test getting template."""
        template = CustomTemplate(
            id="test-template",
            name="Test",
            system_prompt="Prompt",
        )
        config = PromptsConfig(custom_templates=[template])
        assert config.get_template("test-template") == template
        assert config.get_template("nonexistent") is None
    
    def test_config_to_dict(self):
        """Test config serialization."""
        role = PromptRole(id="test", name="Test", system_prompt="Prompt")
        template = CustomTemplate(
            id="tmpl",
            name="Template",
            system_prompt="Prompt",
        )
        config = PromptsConfig(
            active_role="test",
            roles={"test": role},
            custom_templates=[template],
            favorites=["test"],
        )
        data = config.to_dict()
        assert data['active_role'] == "test"
        assert "test" in data['roles']
        assert len(data['custom_templates']) == 1
        assert data['favorites'] == ["test"]
    
    def test_config_from_dict(self):
        """Test config deserialization."""
        data = {
            'active_role': 'test',
            'roles': {
                'test': {
                    'name': 'Test',
                    'system_prompt': 'Prompt',
                    'description': 'Test role',
                }
            },
            'custom_templates': [
                {
                    'id': 'tmpl',
                    'name': 'Template',
                    'system_prompt': 'Prompt',
                }
            ],
            'language_learning': {
                'enabled': True,
                'target_language': 'Deutsch',
            },
        }
        config = PromptsConfig.from_dict(data)
        assert config.active_role == 'test'
        assert 'test' in config.roles
        assert len(config.custom_templates) == 1
        assert config.language_learning.enabled is True


# --- PromptManager Tests ---


class TestPromptManager:
    """Test PromptManager class."""
    
    def test_init_manager(self):
        """Test manager initialization."""
        config = {}
        manager = PromptManager(config)
        assert manager.prompts_config is not None
        # Should have default roles
        assert "developer" in manager.prompts_config.roles
        assert "tutor" in manager.prompts_config.roles
    
    def test_get_active_role(self):
        """Test getting active role."""
        manager = PromptManager({})
        role = manager.get_active_role()
        assert role is not None
        assert role.id == "developer"
    
    def test_set_active_role(self):
        """Test setting active role."""
        manager = PromptManager({})
        success = manager.set_active_role("tutor")
        assert success is True
        assert manager.prompts_config.active_role == "tutor"
        
        success = manager.set_active_role("nonexistent")
        assert success is False
    
    def test_get_active_role_prompt(self):
        """Test getting active role prompt."""
        manager = PromptManager({})
        prompt = manager.get_active_role_prompt()
        assert prompt is not None
        assert "developer" in prompt.lower()
    
    def test_list_roles(self):
        """Test listing roles."""
        manager = PromptManager({})
        roles = manager.list_roles()
        assert len(roles) >= 5  # At least the 5 defaults
        assert "developer" in roles
        assert "tutor" in roles
    
    def test_get_role(self):
        """Test getting specific role."""
        manager = PromptManager({})
        role = manager.get_role("tutor")
        assert role is not None
        assert role.id == "tutor"
        assert role.enabled is True
    
    def test_role_exists(self):
        """Test checking role existence."""
        manager = PromptManager({})
        assert manager.role_exists("developer") is True
        assert manager.role_exists("nonexistent") is False
    
    def test_list_enabled_roles(self):
        """Test listing enabled roles."""
        manager = PromptManager({})
        enabled = manager.list_enabled_roles()
        assert len(enabled) >= 5
        for role in enabled.values():
            assert role.enabled is True
    
    def test_create_template(self):
        """Test creating custom template."""
        manager = PromptManager({})
        template = CustomTemplate(
            id="my-template",
            name="My Template",
            system_prompt="Custom prompt",
        )
        success = manager.create_template(template)
        assert success is True
        assert manager.get_template("my-template") == template
    
    def test_create_duplicate_template(self):
        """Test that duplicate templates fail."""
        manager = PromptManager({})
        template = CustomTemplate(
            id="test",
            name="Test",
            system_prompt="Prompt",
        )
        assert manager.create_template(template) is True
        assert manager.create_template(template) is False
    
    def test_update_template(self):
        """Test updating custom template."""
        manager = PromptManager({})
        template = CustomTemplate(
            id="test",
            name="Test",
            system_prompt="Original",
        )
        manager.create_template(template)
        
        template.system_prompt = "Updated"
        success = manager.update_template(template)
        assert success is True
        assert manager.get_template("test").system_prompt == "Updated"
    
    def test_update_nonexistent_template(self):
        """Test updating non-existent template fails."""
        manager = PromptManager({})
        template = CustomTemplate(
            id="nonexistent",
            name="Test",
            system_prompt="Prompt",
        )
        success = manager.update_template(template)
        assert success is False
    
    def test_delete_template(self):
        """Test deleting custom template."""
        manager = PromptManager({})
        template = CustomTemplate(
            id="test",
            name="Test",
            system_prompt="Prompt",
        )
        manager.create_template(template)
        success = manager.delete_template("test")
        assert success is True
        assert manager.get_template("test") is None
    
    def test_delete_nonexistent_template(self):
        """Test deleting non-existent template fails."""
        manager = PromptManager({})
        success = manager.delete_template("nonexistent")
        assert success is False
    
    def test_list_templates(self):
        """Test listing custom templates."""
        manager = PromptManager({})
        t1 = CustomTemplate(id="t1", name="T1", system_prompt="P1")
        t2 = CustomTemplate(id="t2", name="T2", system_prompt="P2")
        manager.create_template(t1)
        manager.create_template(t2)
        
        templates = manager.list_templates()
        assert len(templates) == 2
    
    def test_search_templates(self):
        """Test searching templates."""
        manager = PromptManager({})
        t1 = CustomTemplate(
            id="t1",
            name="Python Helper",
            system_prompt="P1",
            tags=["python"],
        )
        t2 = CustomTemplate(
            id="t2",
            name="JavaScript Helper",
            system_prompt="P2",
            tags=["javascript"],
        )
        manager.create_template(t1)
        manager.create_template(t2)
        
        results = manager.search_templates("python")
        assert len(results) == 1
        assert results[0].id == "t1"
        
        results = manager.search_templates("helper")
        assert len(results) == 2
    
    def test_add_favorite(self):
        """Test adding favorites."""
        manager = PromptManager({})
        success = manager.add_favorite("developer")
        assert success is True
        assert manager.is_favorite("developer") is True
    
    def test_add_duplicate_favorite(self):
        """Test adding duplicate favorite."""
        manager = PromptManager({})
        assert manager.add_favorite("developer") is True
        assert manager.add_favorite("developer") is False
    
    def test_remove_favorite(self):
        """Test removing favorites."""
        manager = PromptManager({})
        manager.add_favorite("developer")
        success = manager.remove_favorite("developer")
        assert success is True
        assert manager.is_favorite("developer") is False
    
    def test_get_favorites(self):
        """Test getting favorites list."""
        manager = PromptManager({})
        manager.add_favorite("developer")
        manager.add_favorite("tutor")
        
        favorites = manager.get_favorites()
        assert "developer" in favorites
        assert "tutor" in favorites
    
    def test_enable_language_learning(self):
        """Test enabling language learning."""
        manager = PromptManager({})
        success = manager.enable_language_learning("Deutsch", "intermediate")
        assert success is True
        assert manager.is_language_learning_enabled() is True
        
        ll = manager.prompts_config.language_learning
        assert ll.target_language == "Deutsch"
        assert ll.level == LanguageLearningLevel.INTERMEDIATE
    
    def test_enable_language_learning_invalid_level(self):
        """Test enabling language learning with invalid level."""
        manager = PromptManager({})
        success = manager.enable_language_learning("Deutsch", "invalid")
        assert success is False
    
    def test_disable_language_learning(self):
        """Test disabling language learning."""
        manager = PromptManager({})
        manager.enable_language_learning("Deutsch")
        manager.disable_language_learning()
        assert manager.is_language_learning_enabled() is False
    
    def test_get_language_learning_prompt(self):
        """Test getting language learning prompt."""
        manager = PromptManager({})
        
        # Disabled
        prompt = manager.get_language_learning_prompt()
        assert prompt is None
        
        # Enabled
        manager.enable_language_learning("Français", "advanced")
        prompt = manager.get_language_learning_prompt()
        assert prompt is not None
        assert "Français" in prompt
        assert "native-like" in prompt
    
    def test_get_effective_system_prompt_base(self):
        """Test getting base system prompt."""
        manager = PromptManager({})
        manager.set_active_role("developer")
        prompt = manager.get_effective_system_prompt()
        assert prompt is not None
        assert "developer" in prompt.lower()
    
    def test_get_effective_system_prompt_with_ll(self):
        """Test getting system prompt with language learning."""
        manager = PromptManager({})
        manager.set_active_role("developer")
        manager.enable_language_learning("Español")
        
        prompt = manager.get_effective_system_prompt()
        assert "developer" in prompt.lower()
        assert "Español" in prompt
        assert "Language Learning" in prompt
    
    def test_manager_to_dict(self):
        """Test exporting manager config."""
        manager = PromptManager({})
        manager.add_favorite("tutor")
        
        data = manager.to_dict()
        assert 'active_role' in data
        assert 'roles' in data
        assert 'tutor' in data['favorites']
    
    def test_manager_to_config(self):
        """Test exporting config format."""
        manager = PromptManager({})
        config = manager.to_config()
        assert 'prompts' in config
        assert 'active_role' in config['prompts']
    
    def test_manager_with_initial_config(self):
        """Test manager initialization with existing config."""
        initial_config = {
            'prompts': {
                'active_role': 'tutor',
                'favorites': ['tutor', 'developer'],
                'language_learning': {
                    'enabled': True,
                    'target_language': 'Deutsch',
                },
            }
        }
        manager = PromptManager(initial_config)
        assert manager.prompts_config.active_role == 'tutor'
        assert manager.is_language_learning_enabled() is True
        assert manager.is_favorite('tutor') is True


# --- Integration Tests ---


class TestPromptManagerIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_workflow(self):
        """Test a complete workflow."""
        # Initialize
        manager = PromptManager({})
        
        # Create custom template
        template = CustomTemplate(
            id="python-debugging",
            name="Python Debugging",
            system_prompt="Expert Python debugger",
            tags=["python", "debugging"],
        )
        assert manager.create_template(template) is True
        
        # Set as active role (not possible, only roles not templates)
        # But we can add to favorites
        assert manager.add_favorite("python-debugging") is True
        
        # Enable language learning
        assert manager.enable_language_learning("Español", "beginner") is True
        
        # Get effective prompt
        prompt = manager.get_effective_system_prompt()
        assert "developer" in prompt.lower()
        assert "Español" in prompt
        
        # Export configuration
        config = manager.to_config()
        assert config is not None
        
        # Create new manager from exported config
        manager2 = PromptManager(config)
        assert manager2.is_language_learning_enabled() is True
        assert manager2.get_template("python-debugging") is not None
        assert manager2.is_favorite("python-debugging") is True
    
    def test_multiple_templates_and_roles(self):
        """Test managing multiple templates and roles."""
        manager = PromptManager({})
        
        # Create multiple templates
        for i in range(3):
            template = CustomTemplate(
                id=f"template-{i}",
                name=f"Template {i}",
                system_prompt=f"Prompt {i}",
                tags=["test"],
            )
            assert manager.create_template(template) is True
        
        # Verify all created
        templates = manager.list_templates()
        assert len(templates) == 3
        
        # Search by tag
        results = manager.search_templates("test")
        assert len(results) == 3
        
        # Verify all default roles present
        roles = manager.list_roles()
        assert len(roles) >= 5
        
        # Switch roles
        for role_id in ["developer", "tutor", "translator"]:
            assert manager.set_active_role(role_id) is True
            assert manager.get_active_role().id == role_id
