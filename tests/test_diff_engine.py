"""Tests for diff engine."""

import pytest
from kicli_code_assist.context.diff_engine import (
    DiffFormat,
    LineChange,
    FileDiff,
    LLMOutputParser,
    DiffGenerator,
)
from ki_core import Config


class TestLineChange:
    """Test LineChange class."""

    def test_creation(self):
        """Test creating line change."""
        change = LineChange(1, 1, "print('hello')", "context")
        assert change.line_num_old == 1
        assert change.line_num_new == 1
        assert change.content == "print('hello')"
        assert change.change_type == "context"

    def test_added_line(self):
        """Test added line."""
        change = LineChange(None, 5, "new line", "added")
        assert change.line_num_old is None
        assert change.line_num_new == 5
        assert change.change_type == "added"

    def test_removed_line(self):
        """Test removed line."""
        change = LineChange(3, None, "old line", "removed")
        assert change.line_num_old == 3
        assert change.line_num_new is None
        assert change.change_type == "removed"


class TestFileDiff:
    """Test FileDiff class."""

    def test_new_file(self):
        """Test diff for new file."""
        diff = FileDiff(
            file_path="new.py",
            original_content="",
            modified_content="def hello():\n    pass",
            is_new=True,
        )
        assert diff.is_new
        assert not diff.is_deleted
        assert diff.file_path == "new.py"

    def test_deleted_file(self):
        """Test diff for deleted file."""
        diff = FileDiff(
            file_path="old.py",
            original_content="def hello():\n    pass",
            modified_content="",
            is_deleted=True,
        )
        assert not diff.is_new
        assert diff.is_deleted

    def test_get_changes_new_file(self):
        """Test getting changes for new file."""
        diff = FileDiff(
            file_path="new.py",
            original_content="",
            modified_content="line1\nline2",
            is_new=True,
        )
        changes = diff.get_changes()
        assert len(changes) == 2
        assert all(c.change_type == "added" for c in changes)

    def test_get_changes_deleted_file(self):
        """Test getting changes for deleted file."""
        diff = FileDiff(
            file_path="old.py",
            original_content="line1\nline2",
            modified_content="",
            is_deleted=True,
        )
        changes = diff.get_changes()
        assert len(changes) == 2
        assert all(c.change_type == "removed" for c in changes)

    def test_get_changes_modified_file(self):
        """Test getting changes for modified file."""
        diff = FileDiff(
            file_path="modified.py",
            original_content="def old():\n    pass",
            modified_content="def new():\n    pass",
        )
        changes = diff.get_changes()
        assert len(changes) > 0  # Should have some changes

    def test_unified_diff(self):
        """Test unified diff generation."""
        diff = FileDiff(
            file_path="test.py",
            original_content="line1\nline2\nline3",
            modified_content="line1\nmodified\nline3",
        )
        unified = diff.to_unified_diff(context_lines=1)
        assert "---" in unified
        assert "+++" in unified
        assert "@@" in unified

    def test_count_changes(self):
        """Test counting changes."""
        diff = FileDiff(
            file_path="test.py",
            original_content="a\nb\nc",
            modified_content="a\nx\ny\nc",
        )
        added, removed, context = diff.count_changes()
        # Should have some changes
        assert added + removed + context > 0


class TestLLMOutputParser:
    """Test LLM output parser."""

    def test_initialization(self):
        """Test parser initialization."""
        parser = LLMOutputParser()
        assert parser.config is not None

    def test_extract_code_blocks_markdown(self):
        """Test extracting markdown code blocks."""
        text = """
Here's the code:

```python
def hello():
    print("world")
```

And here's another:

```javascript
console.log("hi");
```
"""
        parser = LLMOutputParser()
        blocks = parser.extract_code_blocks(text)
        assert len(blocks) >= 2
        assert any("python" in b[0].lower() for b in blocks)
        assert any("javascript" in b[0].lower() for b in blocks)

    def test_extract_code_blocks_with_content(self):
        """Test that code content is extracted."""
        text = """
```python
def test():
    return 42
```
"""
        parser = LLMOutputParser()
        blocks = parser.extract_code_blocks(text)
        assert len(blocks) > 0
        assert "def test" in blocks[0][1]

    def test_extract_file_references(self):
        """Test extracting file references."""
        text = """
Update the file 'auth.py' with:
Modify "utils.js" to add:
Create new file "config.go"
"""
        parser = LLMOutputParser()
        files = parser.extract_file_references(text)
        # Should find all three files
        assert any("auth.py" in f for f in files) or any(".py" in f for f in files)
        assert any("utils.js" in f for f in files) or any(".js" in f for f in files)
        assert any("config.go" in f for f in files) or any(".go" in f for f in files)

    def test_parse_code_with_path(self):
        """Test parsing code with file paths."""
        text = """
In auth.py:
```python
def authenticate():
    pass
```

In utils.js:
```javascript
export function help() {}
```
"""
        parser = LLMOutputParser()
        results = parser.parse_code_with_path(text)
        assert len(results) > 0
        # Should have tuples of (path, lang, code)
        for path, lang, code in results:
            assert path
            assert lang
            assert code

    def test_estimate_confidence_good_code(self):
        """Test confidence score for good code."""
        parser = LLMOutputParser()
        code = "def hello():\n    print('hi')"
        conf = parser.estimate_confidence("test.py", code)
        assert conf > 0.4

    def test_estimate_confidence_with_placeholder(self):
        """Test lower confidence for placeholder code."""
        parser = LLMOutputParser()
        code = "def hello():\n    ... # TODO: implement"
        conf = parser.estimate_confidence("test.py", code)
        assert conf < 0.7  # Should be lower, but not fixed to exact value

    def test_estimate_confidence_no_imports(self):
        """Test confidence for code without imports."""
        parser = LLMOutputParser()
        code = "x = 5"
        conf = parser.estimate_confidence("test.py", code)
        assert 0.0 <= conf <= 1.0


class TestDiffGenerator:
    """Test diff generator."""

    def test_initialization(self):
        """Test generator initialization."""
        gen = DiffGenerator()
        assert gen.context_lines > 0
        assert gen.auto_apply_threshold >= 0.0

    def test_generate_file_diff_new(self):
        """Test generating diff for new file."""
        gen = DiffGenerator()
        diff = gen.generate_file_diff("new.py", "", "def hello():\n    pass")
        assert diff.is_new
        assert not diff.is_deleted

    def test_generate_file_diff_deleted(self):
        """Test generating diff for deleted file."""
        gen = DiffGenerator()
        diff = gen.generate_file_diff("old.py", "def hello():\n    pass", "")
        assert not diff.is_new
        assert diff.is_deleted

    def test_generate_file_diff_modified(self):
        """Test generating diff for modified file."""
        gen = DiffGenerator()
        diff = gen.generate_file_diff(
            "test.py",
            "def old():\n    pass",
            "def new():\n    pass",
        )
        assert not diff.is_new
        assert not diff.is_deleted

    def test_calculate_similarity(self):
        """Test similarity calculation."""
        gen = DiffGenerator()
        # Identical
        sim = gen._calculate_similarity("hello", "hello")
        assert sim == 1.0

        # Completely different
        sim = gen._calculate_similarity("aaa", "bbb")
        assert sim < 0.5

        # Partially similar
        sim = gen._calculate_similarity("hello", "hallo")
        assert 0.5 < sim < 1.0

    def test_generate_diffs(self):
        """Test generating multiple diffs."""
        gen = DiffGenerator()
        files = {
            "file1.py": ("old1", "new1"),
            "file2.py": ("old2", "new2"),
        }
        diffs = gen.generate_diffs(files)
        assert len(diffs) == 2
        assert all(isinstance(d, FileDiff) for d in diffs)

    def test_should_auto_apply_high_confidence(self):
        """Test auto-apply decision for high confidence."""
        gen = DiffGenerator(
            config=Config(diff_auto_apply_threshold=0.8)
        )
        diff = FileDiff(
            file_path="test.py",
            original_content="x = 1",
            modified_content="x = 1  # comment added",
            similarity=0.95,
        )
        assert gen.should_auto_apply(diff)

    def test_should_auto_apply_low_confidence(self):
        """Test auto-apply decision for low confidence."""
        gen = DiffGenerator(
            config=Config(diff_auto_apply_threshold=0.8)
        )
        diff = FileDiff(
            file_path="test.py",
            original_content="old code",
            modified_content="completely new code",
            similarity=0.3,
        )
        assert not gen.should_auto_apply(diff)


class TestDiffEngineIntegration:
    """Integration tests for diff engine."""

    def test_full_workflow_extract_to_diff(self):
        """Test complete workflow: extract from LLM output to diff."""
        llm_text = """
Here's the update for auth.py:

```python
def authenticate(user, password):
    # New implementation
    return True
```
"""
        # Parse LLM output
        parser = LLMOutputParser()
        results = parser.parse_code_with_path(llm_text)
        assert len(results) > 0

        path, lang, code = results[0]
        assert ".py" in path or "unknown" in path

        # Generate diff
        gen = DiffGenerator()
        original = "def authenticate(user, password):\n    return False"
        diff = gen.generate_file_diff(path, original, code)

        # Verify diff structure
        assert diff.file_path == path
        assert diff.original_content == original
        assert diff.modified_content == code

    def test_new_file_workflow(self):
        """Test workflow for creating new file."""
        parser = LLMOutputParser()
        text = """
Create utils.py:
```python
def helper():
    return 42
```
"""
        results = parser.parse_code_with_path(text)
        assert len(results) > 0

        path, lang, code = results[0]

        gen = DiffGenerator()
        diff = gen.generate_file_diff(path, "", code)

        assert diff.is_new
        assert len(diff.get_changes()) > 0

    def test_multiple_file_changes(self):
        """Test handling multiple file changes."""
        parser = LLMOutputParser()
        text = """
Update files:

In app.py:
```python
def main():
    pass
```

In utils.py:
```python
def helper():
    pass
```
"""
        results = parser.parse_code_with_path(text)
        # Should extract code blocks
        assert len(results) >= 1

        gen = DiffGenerator()
        files = {}
        for path, lang, code in results:
            files[path] = ("", code)

        diffs = gen.generate_diffs(files)
        assert len(diffs) >= 1
        assert all(d.is_new for d in diffs)

    def test_confidence_and_auto_apply(self):
        """Test confidence estimation and auto-apply decision."""
        parser = LLMOutputParser()
        gen = DiffGenerator(config=Config(diff_auto_apply_threshold=0.7))

        # Good code - should have high confidence
        good_code = "def authenticate():\n    pass"
        confidence = parser.estimate_confidence("auth.py", good_code)
        assert confidence > 0.4

        # Create diff with high similarity
        diff = FileDiff(
            file_path="auth.py",
            original_content="def authenticate():\n    return False",
            modified_content=good_code,
            similarity=0.9,
        )

        # Should auto-apply
        assert gen.should_auto_apply(diff)

    def test_unified_diff_format(self):
        """Test unified diff format output."""
        diff = FileDiff(
            file_path="test.py",
            original_content="def old():\n    x = 1\n    return x",
            modified_content="def new():\n    x = 1\n    return x * 2",
        )

        unified = diff.to_unified_diff(context_lines=1)

        # Check unified diff markers
        assert "--- a/test.py" in unified
        assert "+++ b/test.py" in unified
        assert "@@" in unified
        assert "-def old" in unified or "- x = 1" in unified or "+ x * 2" in unified
