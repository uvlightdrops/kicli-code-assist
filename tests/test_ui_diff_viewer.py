"""Tests for diff viewer widgets."""

import pytest
from unittest.mock import Mock, MagicMock
from kicli_code_assist.ui.diff_viewer import (
    DiffViewerState,
    DiffDisplay,
    DiffViewerHeader,
    DiffViewerFooter,
    DiffPanel,
)
from kicli_code_assist.context.diff_engine import FileDiff, LineChange


class MockConfig:
    """Mock configuration."""
    diff_context_lines = 3


class TestDiffViewerState:
    """Test DiffViewerState class."""

    def test_initialization_empty(self):
        """Test creating empty state."""
        state = DiffViewerState(diffs=[])
        assert state.diffs == []
        assert state.current_index == 0
        assert state.applied_indices == set()
        assert state.rejected_indices == set()

    def test_initialization_with_diffs(self):
        """Test creating state with diffs."""
        diffs = [Mock(), Mock(), Mock()]
        state = DiffViewerState(diffs=diffs)
        assert len(state.diffs) == 3
        assert state.current_index == 0

    def test_tracking_applied_indices(self):
        """Test tracking applied diffs."""
        diffs = [Mock(), Mock(), Mock()]
        state = DiffViewerState(diffs=diffs)
        state.applied_indices.add(0)
        state.applied_indices.add(2)
        assert 0 in state.applied_indices
        assert 2 in state.applied_indices
        assert 1 not in state.applied_indices

    def test_tracking_rejected_indices(self):
        """Test tracking rejected diffs."""
        diffs = [Mock(), Mock(), Mock()]
        state = DiffViewerState(diffs=diffs)
        state.rejected_indices.add(1)
        assert 1 in state.rejected_indices
        assert 0 not in state.rejected_indices


class TestDiffDisplay:
    """Test DiffDisplay widget."""

    def test_initialization(self):
        """Test diff display initialization."""
        diff = Mock(spec=FileDiff)
        config = MockConfig()
        display = DiffDisplay(diff, config)
        assert display.diff is diff
        assert display.config is config

    def test_render_added_lines_green(self):
        """Test added lines are green."""
        diff = Mock(spec=FileDiff)
        diff.to_unified_diff.return_value = "+added line"
        config = MockConfig()
        display = DiffDisplay(diff, config)

        output = display.render()
        assert "[green]" in output

    def test_render_removed_lines_red(self):
        """Test removed lines are red."""
        diff = Mock(spec=FileDiff)
        diff.to_unified_diff.return_value = "-removed line"
        config = MockConfig()
        display = DiffDisplay(diff, config)

        output = display.render()
        assert "[red]" in output

    def test_render_hunk_header_yellow(self):
        """Test hunk headers are yellow."""
        diff = Mock(spec=FileDiff)
        diff.to_unified_diff.return_value = "@@ -1,3 +1,4 @@"
        config = MockConfig()
        display = DiffDisplay(diff, config)

        output = display.render()
        assert "[yellow]" in output

    def test_render_file_header_cyan(self):
        """Test file headers are cyan."""
        diff = Mock(spec=FileDiff)
        diff.to_unified_diff.return_value = "--- src/file.py"
        config = MockConfig()
        display = DiffDisplay(diff, config)

        output = display.render()
        assert "[cyan]" in output


class TestDiffViewerHeader:
    """Test DiffViewerHeader widget."""

    def test_header_empty_diffs(self):
        """Test header with no diffs."""
        state = DiffViewerState(diffs=[])
        config = MockConfig()
        header = DiffViewerHeader(state, config)

        output = header.render()
        assert "No diffs" in output

    def test_header_shows_progress(self):
        """Test header shows diff progress."""
        diffs = [Mock(), Mock(), Mock()]
        state = DiffViewerState(diffs=diffs)
        state.current_index = 1
        config = MockConfig()
        header = DiffViewerHeader(state, config)

        diffs[1].similarity = 0.85
        diffs[1].file_path = "src/auth.py"
        diffs[1].get_changes.return_value = [
            Mock(type="added"),
            Mock(type="removed"),
        ]

        output = header.render()
        assert "2/3" in output
        assert "src/auth.py" in output

    def test_header_auto_apply_status(self):
        """Test header shows auto-apply status."""
        diffs = [Mock()]
        diffs[0].similarity = 0.85
        diffs[0].file_path = "test.py"
        diffs[0].get_changes.return_value = []

        state = DiffViewerState(diffs=diffs)
        config = MockConfig()
        header = DiffViewerHeader(state, config)

        output = header.render()
        assert "✅ Auto-apply" in output

    def test_header_review_needed_status(self):
        """Test header shows review needed."""
        diffs = [Mock()]
        diffs[0].similarity = 0.5
        diffs[0].file_path = "test.py"
        diffs[0].get_changes.return_value = []

        state = DiffViewerState(diffs=diffs)
        config = MockConfig()
        header = DiffViewerHeader(state, config)

        output = header.render()
        assert "⚠️ Review" in output

    def test_header_pending_status(self):
        """Test header shows pending status."""
        diffs = [Mock()]
        diffs[0].similarity = 0.8
        diffs[0].file_path = "test.py"
        diffs[0].get_changes.return_value = []

        state = DiffViewerState(diffs=diffs)
        config = MockConfig()
        header = DiffViewerHeader(state, config)

        output = header.render()
        assert "⏳ PENDING" in output

    def test_header_applied_status(self):
        """Test header shows applied status."""
        diffs = [Mock()]
        diffs[0].similarity = 0.8
        diffs[0].file_path = "test.py"
        diffs[0].get_changes.return_value = []

        state = DiffViewerState(diffs=diffs)
        state.applied_indices.add(0)
        config = MockConfig()
        header = DiffViewerHeader(state, config)

        output = header.render()
        assert "✅ APPLIED" in output


class TestDiffViewerFooter:
    """Test DiffViewerFooter widget."""

    def test_footer_shows_keybindings(self):
        """Test footer displays keybindings."""
        footer = DiffViewerFooter()
        output = footer.render()

        assert "[b]j[/b]" in output  # Next
        assert "[b]k[/b]" in output  # Prev
        assert "[b]a[/b]" in output  # Apply
        assert "[b]r[/b]" in output  # Reject
        assert "[b]A[/b]" in output  # Apply all
        assert "[b]q[/b]" in output  # Close


class TestDiffPanel:
    """Test DiffPanel container."""

    def test_initialization(self):
        """Test panel initialization."""
        diffs = [Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        assert panel.state.diffs == diffs
        assert panel.state.current_index == 0
        assert len(panel.state.applied_indices) == 0

    def test_navigate_next(self):
        """Test navigating to next diff."""
        diffs = [Mock(), Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.navigate_next()
        assert panel.state.current_index == 1

        panel.navigate_next()
        assert panel.state.current_index == 2

    def test_navigate_next_bounds(self):
        """Test next navigation doesn't exceed bounds."""
        diffs = [Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.state.current_index = 1
        panel.navigate_next()
        # Should stay at 1
        assert panel.state.current_index == 1

    def test_navigate_prev(self):
        """Test navigating to previous diff."""
        diffs = [Mock(), Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.state.current_index = 2
        panel.navigate_prev()
        assert panel.state.current_index == 1

        panel.navigate_prev()
        assert panel.state.current_index == 0

    def test_navigate_prev_bounds(self):
        """Test prev navigation doesn't go below 0."""
        diffs = [Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.navigate_prev()
        # Should stay at 0
        assert panel.state.current_index == 0

    def test_apply_current_diff(self):
        """Test applying current diff."""
        diffs = [Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.apply_current()
        assert 0 in panel.state.applied_indices

    def test_apply_current_calls_callback(self):
        """Test apply calls callback."""
        diffs = [Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)
        panel.on_diff_applied = Mock()

        panel.apply_current()
        panel.on_diff_applied.assert_called_once()

    def test_reject_current_diff(self):
        """Test rejecting current diff."""
        diffs = [Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.reject_current()
        assert 0 in panel.state.rejected_indices

    def test_reject_current_calls_callback(self):
        """Test reject calls callback."""
        diffs = [Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)
        panel.on_diff_rejected = Mock()

        panel.reject_current()
        panel.on_diff_rejected.assert_called_once()

    def test_apply_all_diffs(self):
        """Test applying all diffs."""
        diffs = [Mock(), Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.apply_all()
        assert len(panel.state.applied_indices) == 3

    def test_cannot_apply_rejected(self):
        """Test cannot apply rejected diff."""
        diffs = [Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.reject_current()
        initial_applied = len(panel.state.applied_indices)

        panel.apply_current()
        # Should not have changed
        assert len(panel.state.applied_indices) == initial_applied

    def test_get_applied_diffs(self):
        """Test getting applied diffs."""
        diffs = [Mock(), Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.state.applied_indices.add(0)
        panel.state.applied_indices.add(2)

        applied = panel.get_applied_diffs()
        assert len(applied) == 2
        assert applied[0][0] == 0
        assert applied[1][0] == 2

    def test_get_rejected_diffs(self):
        """Test getting rejected diffs."""
        diffs = [Mock(), Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.state.rejected_indices.add(1)

        rejected = panel.get_rejected_diffs()
        assert len(rejected) == 1
        assert rejected[0][0] == 1

    def test_get_summary(self):
        """Test getting summary."""
        diffs = [Mock(), Mock(), Mock()]
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        panel.state.applied_indices.add(0)
        panel.state.rejected_indices.add(1)

        summary = panel.get_summary()
        assert summary["total"] == 3
        assert summary["applied"] == 1
        assert summary["rejected"] == 1
        assert summary["pending"] == 1
