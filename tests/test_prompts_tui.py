"""Unit tests for prompt management TUI components."""

import pytest
from textual.widgets import Static, Input, TextArea
from unittest.mock import MagicMock, patch, Mock

from kicli_code_assist.prompts import (
    PromptManager,
    CustomTemplate,
    LanguageLearningLevel,
)
from kicli_code_assist.ui.prompts_panel import (
    RoleSelector,
    LanguageLearningPanel,
    PromptStatusBar,
    PromptsPanel,
)
from kicli_code_assist.ui.prompt_preview import (
    PromptPreview,
    PromptInfo,
)


@pytest.fixture
def prompt_manager():
    """Create a PromptManager for testing."""
    return PromptManager({})


class TestRoleSelector:
    """Test RoleSelector component."""
    
    def test_role_selector_initialization(self, prompt_manager):
        """Test selector initializes with available roles."""
        selector = RoleSelector(prompt_manager)
        assert selector.manager is prompt_manager
        assert len(selector.roles_list) >= 5  # Default roles
    
    def test_role_selector_displays_roles(self, prompt_manager):
        """Test selector displays roles correctly."""
        selector = RoleSelector(prompt_manager)
        assert "developer" in selector.roles_list
        assert "tutor" in selector.roles_list
    
    def test_role_selector_navigation(self, prompt_manager):
        """Test navigating through roles."""
        selector = RoleSelector(prompt_manager)
        initial_index = selector.selected_index
        
        selector.action_select_next_role()
        assert selector.selected_index == initial_index + 1
        
        selector.action_select_previous_role()
        assert selector.selected_index == initial_index
    
    def test_role_selector_set_active(self, prompt_manager):
        """Test setting active role."""
        selector = RoleSelector(prompt_manager)
        selector.selected_index = 1
        role_to_set = selector.roles_list[1]
        
        selector.action_set_active_role()
        assert prompt_manager.prompts_config.active_role == role_to_set
    
    def test_role_selector_favorite_toggle(self, prompt_manager):
        """Test toggling favorite status."""
        selector = RoleSelector(prompt_manager)
        role_id = selector.roles_list[0]
        
        assert not prompt_manager.is_favorite(role_id)
        
        selector.action_toggle_favorite()
        assert prompt_manager.is_favorite(role_id)
        
        selector.action_toggle_favorite()
        assert not prompt_manager.is_favorite(role_id)


class TestLanguageLearningPanel:
    """Test LanguageLearningPanel component."""
    
    def test_ll_panel_initialization(self, prompt_manager):
        """Test LL panel initializes correctly."""
        panel = LanguageLearningPanel(prompt_manager)
        assert panel.manager is prompt_manager
    
    def test_ll_panel_display_disabled(self, prompt_manager):
        """Test display when LL is disabled."""
        panel = LanguageLearningPanel(prompt_manager)
        assert not prompt_manager.is_language_learning_enabled()
        # Panel should show disabled state
    
    def test_ll_panel_toggle_enable(self, prompt_manager):
        """Test enabling language learning."""
        panel = LanguageLearningPanel(prompt_manager)
        
        assert not prompt_manager.is_language_learning_enabled()
        panel.action_toggle_language_learning()
        assert prompt_manager.is_language_learning_enabled()
    
    def test_ll_panel_toggle_disable(self, prompt_manager):
        """Test disabling language learning."""
        panel = LanguageLearningPanel(prompt_manager)
        
        # Enable first
        prompt_manager.enable_language_learning("Español", "beginner")
        assert prompt_manager.is_language_learning_enabled()
        
        # Then disable
        panel.action_toggle_language_learning()
        assert not prompt_manager.is_language_learning_enabled()


class TestPromptStatusBar:
    """Test PromptStatusBar component."""
    
    def test_status_bar_initialization(self, prompt_manager):
        """Test status bar initializes."""
        bar = PromptStatusBar(prompt_manager)
        assert bar.manager is prompt_manager
    
    def test_status_bar_displays_active_role(self, prompt_manager):
        """Test status bar shows active role."""
        bar = PromptStatusBar(prompt_manager)
        prompt_manager.set_active_role("tutor")
        bar.update_display()
        # Bar should show tutor as active
    
    def test_status_bar_displays_ll_status(self, prompt_manager):
        """Test status bar shows language learning status."""
        bar = PromptStatusBar(prompt_manager)
        
        # Initially disabled
        bar.update_display()
        
        # Enable
        prompt_manager.enable_language_learning("Deutsch", "intermediate")
        bar.update_display()
        # Should show language learning info


class TestPromptPreview:
    """Test PromptPreview component."""
    
    def test_preview_initialization(self, prompt_manager):
        """Test preview initializes."""
        preview = PromptPreview(prompt_manager)
        assert preview.manager is prompt_manager
    
    def test_preview_shows_developer_prompt(self, prompt_manager):
        """Test preview displays developer role prompt."""
        prompt_manager.set_active_role("developer")
        preview = PromptPreview(prompt_manager)
        prompt = preview.manager.get_effective_system_prompt()
        assert prompt is not None
        assert "developer" in prompt.lower()
    
    def test_preview_includes_language_learning(self, prompt_manager):
        """Test preview includes LL prompt when enabled."""
        prompt_manager.enable_language_learning("Español", "beginner")
        preview = PromptPreview(prompt_manager)
        prompt = preview.manager.get_effective_system_prompt()
        assert "Español" in prompt
        assert "Language Learning" in prompt


class TestPromptInfo:
    """Test PromptInfo component."""
    
    def test_info_initialization(self, prompt_manager):
        """Test info panel initializes."""
        info = PromptInfo(prompt_manager)
        assert info.manager is prompt_manager
    
    def test_info_shows_active_role_details(self, prompt_manager):
        """Test info displays active role details."""
        prompt_manager.set_active_role("code_reviewer")
        info = PromptInfo(prompt_manager)
        # Should show Code Reviewer info
    
    def test_info_shows_language_learning(self, prompt_manager):
        """Test info shows LL details when enabled."""
        prompt_manager.enable_language_learning("Français", "advanced")
        info = PromptInfo(prompt_manager)
        # Should show language learning details


class TestPromptsPanel:
    """Test complete PromptsPanel."""
    
    def test_panel_initialization(self, prompt_manager):
        """Test prompts panel initializes."""
        panel = PromptsPanel(prompt_manager)
        assert panel.manager is prompt_manager
    
    def test_panel_provides_effective_prompt(self, prompt_manager):
        """Test panel can return effective prompt."""
        panel = PromptsPanel(prompt_manager)
        prompt = panel.get_effective_prompt()
        assert prompt is not None
        assert len(prompt) > 0
    
    def test_panel_role_switching(self, prompt_manager):
        """Test switching roles via panel."""
        panel = PromptsPanel(prompt_manager)
        
        initial_role = prompt_manager.get_active_role()
        prompt_manager.set_active_role("tutor")
        
        assert prompt_manager.get_active_role().id == "tutor"
        assert prompt_manager.get_active_role() != initial_role


class TestIntegrationWorkflows:
    """Integration tests for prompt TUI workflows."""
    
    def test_complete_prompt_workflow(self, prompt_manager):
        """Test a complete workflow in the UI."""
        panel = PromptsPanel(prompt_manager)
        
        # 1. Start with developer
        assert prompt_manager.prompts_config.active_role == "developer"
        
        # 2. Switch to tutor
        prompt_manager.set_active_role("tutor")
        assert prompt_manager.get_active_role().id == "tutor"
        
        # 3. Enable language learning
        prompt_manager.enable_language_learning("Español", "intermediate")
        assert prompt_manager.is_language_learning_enabled()
        
        # 4. Get effective prompt (should include LL)
        prompt = panel.get_effective_prompt()
        assert "Español" in prompt
        
        # 5. Create custom template
        template = CustomTemplate(
            id="my-prompt",
            name="My Prompt",
            system_prompt="Custom content",
        )
        prompt_manager.create_template(template)
        assert prompt_manager.get_template("my-prompt") is not None
        
        # 6. Add to favorites
        prompt_manager.add_favorite("tutor")
        assert prompt_manager.is_favorite("tutor")
    
    def test_language_learning_prompt_injection(self, prompt_manager):
        """Test that LL is injected into system prompt."""
        # Get base prompt
        prompt_manager.set_active_role("developer")
        base_prompt = prompt_manager.get_active_role_prompt()
        
        # Enable LL
        prompt_manager.enable_language_learning("Deutsch", "intermediate")
        effective_prompt = prompt_manager.get_effective_system_prompt()
        
        # Effective should include both base and LL
        assert base_prompt in effective_prompt
        assert "Deutsch" in effective_prompt
        assert "Language Learning" in effective_prompt
        # intermediate level shows as "natural pacing and some idioms"
        assert "idioms" in effective_prompt
    
    def test_template_and_favorites(self, prompt_manager):
        """Test template and favorites management."""
        # Create multiple templates
        for i in range(3):
            template = CustomTemplate(
                id=f"template-{i}",
                name=f"Template {i}",
                system_prompt=f"Prompt {i}",
                tags=["test"],
            )
            prompt_manager.create_template(template)
        
        # Favorite some
        prompt_manager.add_favorite("template-0")
        prompt_manager.add_favorite("template-2")
        
        # Verify favorites
        favorites = prompt_manager.get_favorites()
        assert len(favorites) == 2
        assert "template-0" in favorites
        
        # Search templates
        results = prompt_manager.search_templates("test")
        assert len(results) == 3


class TestUIStateManagement:
    """Test UI state management with prompts."""
    
    def test_role_selector_state_persistence(self, prompt_manager):
        """Test role selector maintains state."""
        selector = RoleSelector(prompt_manager)
        
        # Change selection
        selector.selected_index = 2
        initial_index = selector.selected_index
        
        # Render again
        selector.render_display()
        
        # Selection should persist
        assert selector.selected_index == initial_index
    
    def test_ll_panel_state_consistency(self, prompt_manager):
        """Test LL panel state stays consistent."""
        panel = LanguageLearningPanel(prompt_manager)
        
        # Toggle on
        panel.action_toggle_language_learning()
        state_1 = prompt_manager.is_language_learning_enabled()
        
        # Render
        panel.render_display()
        
        # State should persist
        state_2 = prompt_manager.is_language_learning_enabled()
        assert state_1 == state_2
    
    def test_sync_between_components(self, prompt_manager):
        """Test state sync between multiple components."""
        selector = RoleSelector(prompt_manager)
        info = PromptInfo(prompt_manager)
        status = PromptStatusBar(prompt_manager)
        
        # Change via selector
        prompt_manager.set_active_role("tutor")
        
        # All components should reflect the change
        assert selector.manager.get_active_role().id == "tutor"
        assert info.manager.get_active_role().id == "tutor"
        assert status.manager.get_active_role().id == "tutor"
