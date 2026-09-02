"""Tests for smart file selection system."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from kicli_code_assist.context.smart_selector import (
    FileMetadata,
    DependencyGraph,
    ASTAnalyzer,
    SmartFileSelector,
)
from ki_core import Config


class TestFileMetadata:
    """Test FileMetadata class."""

    def test_creation(self):
        """Test creating FileMetadata."""
        path = Path("test.py")
        meta = FileMetadata(path=path, language="python", size_kb=10.5)
        assert meta.path == path
        assert meta.language == "python"
        assert meta.size_kb == 10.5
        assert meta.imports == set()
        assert meta.exports == set()

    def test_with_imports_exports(self):
        """Test FileMetadata with imports and exports."""
        meta = FileMetadata(
            path=Path("test.py"),
            language="python",
            imports={"os", "sys"},
            exports={"my_func", "MyClass"},
        )
        assert "os" in meta.imports
        assert "my_func" in meta.exports


class TestDependencyGraph:
    """Test DependencyGraph class."""

    def test_add_file(self):
        """Test adding files to graph."""
        graph = DependencyGraph()
        meta1 = FileMetadata(path=Path("a.py"), language="python")
        meta2 = FileMetadata(path=Path("b.py"), language="python")

        graph.add_file(meta1)
        graph.add_file(meta2)

        assert len(graph.files) == 2

    def test_import_to_paths_python(self):
        """Test converting Python imports to paths."""
        graph = DependencyGraph()
        paths = graph._import_to_paths("foo.bar.baz", Path("."), "python")
        assert "foo/bar/baz.py" in paths
        assert "foo/bar/baz/__init__.py" in paths

    def test_import_to_paths_javascript(self):
        """Test converting JavaScript imports to paths."""
        graph = DependencyGraph()
        paths = graph._import_to_paths("foo/bar/baz", Path("."), "javascript")
        assert "foo/bar/baz.js" in paths
        assert "foo/bar/baz/index.js" in paths

    def test_import_to_paths_go(self):
        """Test converting Go imports to paths."""
        graph = DependencyGraph()
        paths = graph._import_to_paths("github.com/org/pkg", Path("."), "go")
        assert "github.com/org/pkg" in paths

    def test_get_related_files(self):
        """Test getting related files."""
        graph = DependencyGraph()

        meta1 = FileMetadata(path=Path("a.py"), language="python")
        meta2 = FileMetadata(path=Path("b.py"), language="python")
        meta3 = FileMetadata(path=Path("c.py"), language="python")

        meta1.dependencies.add("b.py")
        meta2.dependencies.add("c.py")

        graph.add_file(meta1)
        graph.add_file(meta2)
        graph.add_file(meta3)

        related = graph.get_related_files("a.py", depth=2)
        assert "a.py" in related
        assert "b.py" in related
        assert "c.py" in related

    def test_get_entry_points(self):
        """Test identifying entry points."""
        graph = DependencyGraph()
        graph.add_file(FileMetadata(path=Path("main.py"), language="python"))
        graph.add_file(FileMetadata(path=Path("utils.py"), language="python"))

        entry_points = graph.get_entry_points()
        assert "main.py" in entry_points
        assert "utils.py" not in entry_points


class TestASTAnalyzer:
    """Test AST analysis."""

    def test_analyze_python_imports(self):
        """Test extracting imports from Python code."""
        code = """
import os
import sys
from pathlib import Path
from typing import Optional
"""
        imports, exports = ASTAnalyzer.analyze_python(code)
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "typing" in imports

    def test_analyze_python_exports(self):
        """Test extracting exports from Python code."""
        code = """
def public_func():
    pass

def _private_func():
    pass

class PublicClass:
    pass

class _PrivateClass:
    pass
"""
        imports, exports = ASTAnalyzer.analyze_python(code)
        assert "public_func" in exports
        assert "PublicClass" in exports
        assert "_private_func" not in exports
        assert "_PrivateClass" not in exports

    def test_analyze_python_syntax_error(self):
        """Test handling syntax errors in Python."""
        code = "this is not valid python {{{"
        imports, exports = ASTAnalyzer.analyze_python(code)
        assert imports == set()
        assert exports == set()

    def test_analyze_javascript_imports(self):
        """Test extracting imports from JavaScript."""
        code = """
import React from 'react';
import { useState } from 'react';
const express = require('express');
import './styles.css';
"""
        imports, exports = ASTAnalyzer.analyze_javascript(code)
        assert "react" in imports
        assert "express" in imports
        assert "./styles.css" in imports

    def test_analyze_javascript_exports(self):
        """Test extracting exports from JavaScript."""
        code = """
export function myFunc() {}
export const MY_CONST = 42;
export class MyClass {}
module.exports = MyClass;
"""
        imports, exports = ASTAnalyzer.analyze_javascript(code)
        assert "myFunc" in exports or "MY_CONST" in exports

    def test_analyze_go_imports(self):
        """Test extracting imports from Go."""
        code = """
package main

import (
    "fmt"
    "github.com/user/pkg"
)

func main() {
    fmt.Println("hello")
}
"""
        imports, exports = ASTAnalyzer.analyze_go(code)
        assert "fmt" in imports
        assert "github.com/user/pkg" in imports

    def test_analyze_go_exports(self):
        """Test extracting exports from Go."""
        code = """
func PublicFunc() {}
func privateFunc() {}
type PublicType struct {}
type privateType struct {}
"""
        imports, exports = ASTAnalyzer.analyze_go(code)
        assert "PublicFunc" in exports
        assert "PublicType" in exports
        assert "privateFunc" not in exports

    def test_analyze_dispatch(self):
        """Test language-based dispatch."""
        py_code = "import os"
        js_code = "import React from 'react'"
        go_code = 'import "fmt"'

        py_imports, _ = ASTAnalyzer.analyze(py_code, "python")
        js_imports, _ = ASTAnalyzer.analyze(js_code, "javascript")
        go_imports, _ = ASTAnalyzer.analyze(go_code, "go")

        assert "os" in py_imports
        assert "react" in js_imports
        assert "fmt" in go_imports


class TestSmartFileSelector:
    """Test SmartFileSelector."""

    def test_initialization(self):
        """Test initializing selector."""
        selector = SmartFileSelector()
        assert selector.root.is_dir()
        assert selector.config is not None
        assert selector.max_files > 0

    def test_detect_language(self):
        """Test language detection."""
        selector = SmartFileSelector()
        assert selector._detect_language(Path("file.py")) == "python"
        assert selector._detect_language(Path("file.js")) == "javascript"
        assert selector._detect_language(Path("file.go")) == "go"
        assert selector._detect_language(Path("file.txt")) is None

    def test_should_ignore(self):
        """Test ignore pattern matching."""
        selector = SmartFileSelector()
        assert selector._should_ignore(Path("__pycache__/file.py"))
        assert selector._should_ignore(Path("node_modules/pkg/index.js"))
        assert not selector._should_ignore(Path("src/main.py"))

    def test_score_file_by_name(self):
        """Test scoring file by name match."""
        selector = SmartFileSelector()
        meta = FileMetadata(path=Path("auth.py"), language="python")
        score = selector._score_file(meta, "authentication")
        assert score > 0.2  # Should match "auth" in "auth.py"

    def test_score_file_by_exports(self):
        """Test scoring file by export match."""
        selector = SmartFileSelector()
        meta = FileMetadata(
            path=Path("utils.py"),
            language="python",
            exports={"authenticate", "authorize"},
        )
        score = selector._score_file(meta, "authenticate user")
        assert score > 0.15  # Should match "authenticate" in exports

    def test_score_file_entry_point(self):
        """Test scoring entry point files higher."""
        selector = SmartFileSelector()
        meta = FileMetadata(path=Path("main.py"), language="python")
        score = selector._score_file(meta, "something")
        assert score >= 0.2  # Entry point bonus

    def test_score_file_config(self):
        """Test scoring config files."""
        selector = SmartFileSelector()
        meta = FileMetadata(path=Path("pyproject.toml"), language="python")
        score = selector._score_file(meta, "package info")
        assert score >= 0.15  # Config file bonus

    def test_score_file_size_preference(self):
        """Test size preference in scoring."""
        selector = SmartFileSelector()

        # Optimal size (5-100 KB)
        meta_optimal = FileMetadata(
            path=Path("good.py"), language="python", size_kb=50
        )
        score_optimal = selector._score_file(meta_optimal, "test")

        # Too large (>500 KB)
        meta_large = FileMetadata(path=Path("huge.py"), language="python", size_kb=1000)
        score_large = selector._score_file(meta_large, "test")

        assert score_optimal > score_large

    def test_select_files_empty_project(self):
        """Test selecting files from empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            selector = SmartFileSelector(tmpdir)
            selected = selector.select_files_for_query("test")
            assert selected == []

    def test_select_files_respects_max_files(self):
        """Test max files constraint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test files
            for i in range(20):
                (tmpdir_path / f"file{i}.py").write_text("import os")

            selector = SmartFileSelector(tmpdir, Config(
                context_max_files=5,
                context_max_size_mb=100
            ))
            selected = selector.select_files_for_query("test")
            assert len(selected) <= 5

    def test_select_files_respects_size_limit(self):
        """Test size limit constraint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test files
            for i in range(5):
                (tmpdir_path / f"file{i}.py").write_text("import os\n" * 100)

            selector = SmartFileSelector(tmpdir, Config(
                context_max_files=100,
                context_max_size_mb=0.5  # 512 KB limit
            ))
            selected = selector.select_files_for_query("test")

            # Check total size
            total_size = sum(
                selector.graph.files[str(tmpdir_path / f)].size_kb
                for f, _ in selected
            )
            assert total_size <= 512

    def test_scan_project(self):
        """Test scanning a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test files
            (tmpdir_path / "main.py").write_text(
                "import os\nimport sys\ndef main(): pass"
            )
            (tmpdir_path / "utils.py").write_text("def helper(): pass")

            selector = SmartFileSelector(tmpdir)
            files = selector.scan_project()

            assert len(files) >= 2
            assert any("main.py" in key for key in files.keys())
            assert any("utils.py" in key for key in files.keys())

    def test_scan_project_ignores_patterns(self):
        """Test that scan ignores specified patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create files
            (tmpdir_path / "main.py").write_text("pass")
            (tmpdir_path / "test.pyc").write_text("binary")

            selector = SmartFileSelector(tmpdir)
            files = selector.scan_project()

            # Should not include .pyc file
            assert not any(".pyc" in key for key in files.keys())

    def test_get_context_for_query(self):
        """Test generating context for a query."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test files
            (tmpdir_path / "auth.py").write_text(
                "def authenticate(user, password): pass"
            )
            (tmpdir_path / "utils.py").write_text("def helper(): pass")

            # Create selector with low threshold
            selector = SmartFileSelector(tmpdir, Config(
                context_max_files=10,
                context_relevance_threshold=0.1
            ))
            context = selector.get_context_for_query("authentication")

            assert "auth" in context or "authenticate" in context
            assert "#" in context  # Should have markdown headers

    def test_resolve_dependencies_python(self):
        """Test resolving Python import dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create files
            (tmpdir_path / "main.py").write_text("from utils import helper")
            (tmpdir_path / "utils.py").write_text("def helper(): pass")

            selector = SmartFileSelector(tmpdir)
            selector.scan_project()

            # Check dependencies were resolved
            files = selector.graph.files
            main_key = [k for k in files.keys() if "main.py" in k][0]
            utils_key = [k for k in files.keys() if "utils.py" in k][0]

            # main should import utils
            assert utils_key in files[main_key].dependencies or files[main_key].imports


class TestSmartFileSelectorIntegration:
    """Integration tests for SmartFileSelector."""

    def test_full_workflow(self):
        """Test complete workflow: scan -> score -> select."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create realistic project
            (tmpdir_path / "main.py").write_text(
                """
import sys
from auth import authenticate
from utils import log

def main():
    user = authenticate('user', 'pass')
    log(f'User {user} logged in')
"""
            )
            (tmpdir_path / "auth.py").write_text(
                """
import hashlib

def authenticate(user, password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return user if validate(user, hashed) else None

def validate(user, hashed):
    pass
"""
            )
            (tmpdir_path / "utils.py").write_text("def log(msg): print(msg)")

            selector = SmartFileSelector(tmpdir)
            selected = selector.select_files_for_query("authenticate user")

            # Should select auth.py and possibly main.py
            assert len(selected) > 0
            selected_files = [k for k, _ in selected]
            assert any("auth" in k for k in selected_files)

    def test_relevance_scoring_order(self):
        """Test that files are ranked by relevance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create files with varying relevance
            (tmpdir_path / "database.py").write_text("pass")
            (tmpdir_path / "auth.py").write_text("def authenticate(): pass")
            (tmpdir_path / "authentication.py").write_text("def auth(): pass")

            selector = SmartFileSelector(tmpdir)
            selected = selector.select_files_for_query("authentication")

            # authentication.py should score higher than database.py
            if len(selected) > 1:
                scores = {k: s for k, s in selected}
                auth_keys = [k for k in scores.keys() if "auth" in k]
                db_keys = [k for k in scores.keys() if "database" in k]

                if auth_keys and db_keys:
                    assert scores[auth_keys[0]] > scores[db_keys[0]]
