"""Unit tests for prompts CLI functions."""

import pytest
from pathlib import Path
from unittest.mock import patch
import yaml
from kicli_code_assist.cli_prompts import (
    list_roles, show_role, set_active_role,
    list_templates, show_template, create_template, delete_template,
    add_favorite, remove_favorite,
    enable_language_learning, disable_language_learning, show_language_learning,
    export_config, import_config
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temp directory with test config."""
    config_file = tmp_path / "ki.yaml"
    config_file.write_text(yaml.dump({
        'prompts': {
            'active_role': 'developer',
            'roles': {},
            'custom_templates': [],
            'language_learning': {
                'enabled': False,
                'target_language': '',
                'native_language': 'English',
                'level': 'beginner',
            },
            'favorites': [],
        }
    }))
    return tmp_path, str(config_file)


class TestListRoles:
    """Test list_roles function."""
    
    def test_list_roles(self, temp_config_dir, capsys):
        """Test listing available roles."""
        tmp_path, config_file = temp_config_dir
        list_roles(config_file)
        captured = capsys.readouterr()
        assert "Developer" in captured.out
        assert "Tutor" in captured.out


class TestShowRole:
    """Test show_role function."""
    
    def test_show_role(self, temp_config_dir, capsys):
        """Test showing role details."""
        tmp_path, config_file = temp_config_dir
        show_role("developer", config_file)
        captured = capsys.readouterr()
        assert "Developer" in captured.out


class TestSetActiveRole:
    """Test set_active_role function."""
    
    def test_set_active_role(self, temp_config_dir, capsys):
        """Test setting active role."""
        tmp_path, config_file = temp_config_dir
        set_active_role("tutor", config_file)
        captured = capsys.readouterr()
        assert "tutor" in captured.out.lower()


class TestListTemplates:
    """Test list_templates function."""
    
    def test_list_templates_empty(self, temp_config_dir, capsys):
        """Test listing templates when none exist."""
        tmp_path, config_file = temp_config_dir
        list_templates(config_file)
        captured = capsys.readouterr()
        # Should show empty or no templates message


class TestShowTemplate:
    """Test show_template function."""
    
    def test_show_template_not_found(self, temp_config_dir):
        """Test showing non-existent template."""
        tmp_path, config_file = temp_config_dir
        from typer.exceptions import Exit
        with pytest.raises(Exit):
            show_template("nonexistent", config_file)


class TestCreateTemplate:
    """Test create_template function."""
    
    def test_create_template(self, temp_config_dir, capsys):
        """Test creating a template."""
        tmp_path, config_file = temp_config_dir
        create_template(
            "test-template",
            "Test Template",
            "This is a test prompt",
            config_file,
            "Test description",
            ["test", "demo"]
        )
        captured = capsys.readouterr()
        
        # Verify config was updated
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert len(config['prompts']['custom_templates']) > 0


class TestDeleteTemplate:
    """Test delete_template function."""
    
    def test_delete_nonexistent_template(self, temp_config_dir):
        """Test deleting non-existent template."""
        tmp_path, config_file = temp_config_dir
        from typer.exceptions import Exit
        with pytest.raises(Exit):
            delete_template("nonexistent", config_file)


class TestFavorites:
    """Test favorite functions."""
    
    def test_add_favorite(self, temp_config_dir, capsys):
        """Test adding favorite."""
        tmp_path, config_file = temp_config_dir
        add_favorite("developer", config_file)
        captured = capsys.readouterr()
        
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert "developer" in config['prompts']['favorites']
    
    def test_remove_favorite(self, temp_config_dir, capsys):
        """Test removing favorite."""
        tmp_path, config_file = temp_config_dir
        # First add, then remove
        add_favorite("developer", config_file)
        remove_favorite("developer", config_file)
        
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert "developer" not in config['prompts']['favorites']


class TestLanguageLearning:
    """Test language learning functions."""
    
    def test_enable_language_learning(self, temp_config_dir, capsys):
        """Test enabling language learning."""
        tmp_path, config_file = temp_config_dir
        enable_language_learning("Spanish", config_file, "beginner", "English")
        captured = capsys.readouterr()
        
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config['prompts']['language_learning']['enabled']
    
    def test_disable_language_learning(self, temp_config_dir, capsys):
        """Test disabling language learning."""
        tmp_path, config_file = temp_config_dir
        enable_language_learning("Spanish", config_file)
        disable_language_learning(config_file)
        
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert not config['prompts']['language_learning']['enabled']
    
    def test_show_language_learning(self, temp_config_dir, capsys):
        """Test showing language learning config."""
        tmp_path, config_file = temp_config_dir
        show_language_learning(config_file)
        captured = capsys.readouterr()


class TestExportImport:
    """Test export and import functions."""
    
    def test_export_config(self, temp_config_dir):
        """Test exporting config."""
        tmp_path, config_file = temp_config_dir
        output_file = tmp_path / "export.yaml"
        
        export_config(str(output_file), config_file)
        
        assert output_file.exists()
        with open(output_file) as f:
            exported = yaml.safe_load(f)
        assert 'prompts' in exported
    
    def test_import_config(self, temp_config_dir):
        """Test importing config."""
        tmp_path, config_file = temp_config_dir
        
        # Create import file
        import_file = tmp_path / "import.yaml"
        import_file.write_text(yaml.dump({
            'prompts': {
                'active_role': 'tutor'
            }
        }))
        
        import_config(str(import_file), config_file)
        
        # Verify config was updated
        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config['prompts']['active_role'] == 'tutor'


class TestIntegrationWorkflows:
    """Integration tests for complete workflows."""
    
    def test_complete_workflow(self, temp_config_dir):
        """Test complete workflow: create template, set favorite, enable LL."""
        tmp_path, config_file = temp_config_dir
        
        # Create template
        create_template(
            "workflow-test",
            "Workflow Test",
            "Test prompt",
            config_file
        )
        
        # Add to favorites
        add_favorite("workflow-test", config_file)
        
        # Enable LL
        enable_language_learning("French", config_file)
        
        # Verify all changes persisted
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        assert len(config['prompts']['custom_templates']) > 0
        assert "workflow-test" in config['prompts']['favorites']
        assert config['prompts']['language_learning']['enabled']
        assert config['prompts']['language_learning']['target_language'] == "French"
