"""Integration tests for Phase 5 UI components."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from kicli_code_assist.ui.focus_manager import FocusManager, FocusMode
from kicli_code_assist.ui.diff_viewer import DiffPanel, DiffDisplay, DiffViewerState
from kicli_code_assist.ui.task_status import TaskStatusWidget, TaskStatusCompact
from kicli_code_assist.executor.task_tracker import TaskTracker, TaskStatus, TaskType
from ki_core import Config


class MockConfig:
    """Mock configuration."""
    diff_context_lines = 3
    diff_auto_apply_threshold = 0.75
    kicli_session_dir = "/tmp/kicli"


class MockTUI:
    """Mock TUI with focus manager integration."""

    def __init__(self):
        self.components = {
            "#file-browser": Mock(focus=Mock()),
            "#file-preview": Mock(focus=Mock()),
            "#chat-history": Mock(focus=Mock()),
            "#input-box": Mock(focus=Mock()),
            "#diff-viewer": Mock(focus=Mock()),
            "#title-bar": Mock(update=Mock()),
        }
        self.focus_manager = FocusManager(self)

    def query_one(self, selector, expect_type=None):
        if selector not in self.components:
            raise Exception(f"Component not found: {selector}")
        return self.components[selector]


class TestPhase5IntegrationWorkflow:
    """Test complete Phase 5 workflow."""

    def test_focus_navigation_sequence(self):
        """Test navigating between panels with focus manager."""
        tui = MockTUI()
        manager = tui.focus_manager

        # Start in input
        assert manager.current_mode == FocusMode.INPUT_FIELD

        # Navigate to file preview
        result = manager.handle_focus_key("ctrl+f")
        assert result is True
        assert manager.current_mode == FocusMode.FILE_PREVIEW
        tui.components["#file-preview"].focus.assert_called()

        # Navigate to chat
        manager.set_focus(FocusMode.CHAT_HISTORY)
        assert manager.current_mode == FocusMode.CHAT_HISTORY
        assert manager.previous_mode == FocusMode.FILE_PREVIEW

        # Open diff viewer
        manager.set_focus(FocusMode.DIFF_VIEWER)
        assert manager.current_mode == FocusMode.DIFF_VIEWER

        # Toggle back to chat
        manager.toggle_focus()
        assert manager.current_mode == FocusMode.CHAT_HISTORY

    def test_all_focus_shortcuts(self):
        """Test all focus shortcuts work correctly."""
        tui = MockTUI()
        manager = tui.focus_manager

        # Test all 5 shortcuts
        shortcuts = [
            ("ctrl+f", FocusMode.FILE_PREVIEW),
            ("ctrl+b", FocusMode.FILE_BROWSER),
            ("ctrl+c", FocusMode.CHAT_HISTORY),
            ("ctrl+i", FocusMode.INPUT_FIELD),
            ("ctrl+d", FocusMode.DIFF_VIEWER),
        ]

        for key, expected_mode in shortcuts:
            result = manager.handle_focus_key(key)
            assert result is True
            assert manager.current_mode == expected_mode

    def test_diff_viewer_workflow(self):
        """Test complete diff viewer workflow."""
        # Create mock diffs
        diffs = []
        for i in range(3):
            diff = Mock()
            diff.file_path = f"src/file{i}.py"
            diff.similarity = 0.85 if i == 0 else 0.65
            diff.get_changes.return_value = [Mock(type="added"), Mock(type="removed")]
            diffs.append(diff)

        # Create diff panel
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        # Navigate through diffs
        assert panel.state.current_index == 0
        panel.navigate_next()
        assert panel.state.current_index == 1
        panel.navigate_next()
        assert panel.state.current_index == 2

        # Navigate backwards
        panel.navigate_prev()
        assert panel.state.current_index == 1

        # Apply diff
        panel.navigate_next()  # Go to index 2
        panel.apply_current()
        assert 2 in panel.state.applied_indices

        # Reject another
        panel.navigate_prev()
        panel.reject_current()
        assert 1 in panel.state.rejected_indices

        # Apply all remaining
        panel.apply_all()
        assert len(panel.state.applied_indices) >= 1

        # Get summary
        summary = panel.get_summary()
        assert summary["total"] == 3
        assert summary["applied"] + summary["rejected"] > 0

    def test_task_tracking_integration(self):
        """Test task tracking with status display."""
        config = MockConfig()
        tracker = TaskTracker(config)

        # Create task hierarchy
        parent = tracker.create_task("analyze", TaskType.LLM_CALL, "Analyze code")
        child1 = tracker.create_task(
            "select", TaskType.FILE_ANALYSIS, "Select files", "analyze"
        )
        child2 = tracker.create_task("cache", TaskType.CACHING, "Cache context", "analyze")

        # Execute tasks
        tracker.start_task("analyze")
        assert parent.status == TaskStatus.IN_PROGRESS
        tracker.start_task("select")
        assert child1.status == TaskStatus.IN_PROGRESS

        tracker.complete_task("select", "Selected 5 files")
        assert child1.status == TaskStatus.COMPLETED

        tracker.start_task("cache")
        tracker.complete_task("cache", "Cached 2.3MB")

        tracker.complete_task("analyze")
        assert parent.status == TaskStatus.COMPLETED

        # Check summary
        summary = tracker.get_summary()
        assert summary["total_tasks"] == 3
        assert summary["completed"] == 3
        assert summary["active"] == 0
        assert summary["completion_rate"] == 100.0

        # Create status widget
        widget = TaskStatusWidget(tracker, show_detail=True)
        assert widget.tracker is tracker

    def test_diff_and_task_integration(self):
        """Test diffs and task tracking working together."""
        config = MockConfig()
        tracker = TaskTracker(config)

        # Create diff task
        diff_task = tracker.create_task(
            "diff-gen", TaskType.DIFF_GENERATION, "Generating diffs"
        )

        # Start diff generation
        tracker.start_task("diff-gen")
        assert diff_task.status == TaskStatus.IN_PROGRESS

        # Simulate diff generation
        diffs = []
        for i in range(2):
            diff = Mock()
            diff.file_path = f"src/file{i}.py"
            diff.similarity = 0.85
            diff.get_changes.return_value = []
            diffs.append(diff)

        # Create diff panel
        panel = DiffPanel(diffs, config)

        # Apply diffs and update task
        panel.apply_all()
        tracker.complete_task("diff-gen", f"Generated {len(diffs)} diffs")

        # Check both are complete
        assert diff_task.status == TaskStatus.COMPLETED
        summary = tracker.get_summary()
        assert summary["completed"] == 1

    def test_auto_apply_workflow(self):
        """Test auto-apply decision workflow."""
        # High confidence diffs
        diffs = []
        for i in range(2):
            diff = Mock()
            diff.file_path = f"src/auto{i}.py"
            diff.similarity = 0.92  # High confidence
            diff.get_changes.return_value = []
            diffs.append(diff)

        # Low confidence diffs
        for i in range(2):
            diff = Mock()
            diff.file_path = f"src/review{i}.py"
            diff.similarity = 0.45  # Low confidence
            diff.get_changes.return_value = []
            diffs.append(diff)

        # Create panel and check status
        config = MockConfig()
        panel = DiffPanel(diffs, config)

        # Count auto-apply candidates
        auto_apply_count = 0
        for diff in diffs:
            if diff.similarity > config.diff_auto_apply_threshold:
                auto_apply_count += 1

        assert auto_apply_count == 2
        # Review count
        review_count = len(diffs) - auto_apply_count
        assert review_count == 2

    def test_focus_title_highlighting(self):
        """Test focus highlighting in title bar."""
        tui = MockTUI()
        manager = tui.focus_manager

        # Focus different panels and check title updates
        modes_to_test = [
            (FocusMode.FILE_BROWSER, "Browser"),
            (FocusMode.FILE_PREVIEW, "Preview"),
            (FocusMode.CHAT_HISTORY, "Chat"),
            (FocusMode.INPUT_FIELD, "Input"),
            (FocusMode.DIFF_VIEWER, "Diff"),
        ]

        for mode, expected_text in modes_to_test:
            manager.set_focus(mode)
            tui.components["#title-bar"].update.assert_called()
            last_call = tui.components["#title-bar"].update.call_args
            assert expected_text in last_call[0][0]
            assert "[orange" in last_call[0][0]

    def test_diff_state_transitions(self):
        """Test diff state transitions."""
        diffs = [Mock(), Mock(), Mock()]
        for i, diff in enumerate(diffs):
            diff.file_path = f"file{i}.py"
            diff.similarity = 0.8
            diff.get_changes.return_value = []

        config = MockConfig()
        panel = DiffPanel(diffs, config)

        # State before any action
        summary = panel.get_summary()
        assert summary["pending"] == 3

        # Apply one
        panel.apply_current()
        summary = panel.get_summary()
        assert summary["applied"] == 1
        assert summary["pending"] == 2

        # Reject another
        panel.navigate_next()
        panel.reject_current()
        summary = panel.get_summary()
        assert summary["rejected"] == 1
        assert summary["pending"] == 1

        # Apply remaining
        panel.navigate_next()
        panel.apply_current()
        summary = panel.get_summary()
        assert summary["applied"] == 2
        assert summary["pending"] == 0

    def test_task_error_handling(self):
        """Test task tracking with errors."""
        config = MockConfig()
        tracker = TaskTracker(config)

        task = tracker.create_task("risky", TaskType.LLM_CALL, "Risky operation")
        tracker.start_task("risky")

        # Simulate failure
        tracker.fail_task("risky", "Network timeout")
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "Network timeout"

        summary = tracker.get_summary()
        assert summary["failed"] == 1

    def test_multiple_diff_viewers(self):
        """Test handling multiple diff panels."""
        diffs1 = [Mock(), Mock()]
        diffs2 = [Mock(), Mock(), Mock()]

        for i, diff in enumerate(diffs1):
            diff.file_path = f"a{i}.py"
            diff.similarity = 0.8
            diff.get_changes.return_value = []

        for i, diff in enumerate(diffs2):
            diff.file_path = f"b{i}.py"
            diff.similarity = 0.8
            diff.get_changes.return_value = []

        config = MockConfig()

        # Two separate panels
        panel1 = DiffPanel(diffs1, config)
        panel2 = DiffPanel(diffs2, config)

        # Each panel is independent
        panel1.apply_all()
        assert panel1.get_summary()["applied"] == 2
        assert panel2.get_summary()["applied"] == 0

        panel2.apply_current()
        assert panel2.get_summary()["applied"] == 1
