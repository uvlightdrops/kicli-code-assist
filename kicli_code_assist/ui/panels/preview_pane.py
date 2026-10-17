"""File preview pane."""

from pathlib import Path
from textual.widgets import Static


class PreviewPane(Static):
    """Scrollable preview with line selection support."""

    can_focus = True

    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
        self.lines: list[str] = []
        self.file_path: Path | None = None
        self.cursor_line = 0
        self.selection_start: int | None = None
        self.selection_end: int | None = None
        self.preview_scroll_offset = 0
        self.page_size = 20

    def set_content(self, path: Path, lines: list[str]) -> None:
        """Load preview content for a file."""
        self.file_path = path
        self.lines = lines
        self.cursor_line = 0
        self.selection_start = None
        self.selection_end = None
        self.preview_scroll_offset = 0
        self._refresh_preview()

    def action_cursor_down(self) -> None:
        """Move cursor down one line."""
        if self.cursor_line < max(0, len(self.lines) - 1):
            self.cursor_line += 1
            self._ensure_cursor_visible()
            self._refresh_preview()

    def action_cursor_up(self) -> None:
        """Move cursor up one line."""
        if self.cursor_line > 0:
            self.cursor_line -= 1
            self._ensure_cursor_visible()
            self._refresh_preview()

    def action_page_down(self) -> None:
        """Scroll down like less/more."""
        if self.lines:
            self.cursor_line = min(len(self.lines) - 1, self.cursor_line + self.page_size)
            self._ensure_cursor_visible()
            self._refresh_preview()

    def action_page_up(self) -> None:
        """Scroll up like less/more."""
        if self.lines:
            self.cursor_line = max(0, self.cursor_line - self.page_size)
            self._ensure_cursor_visible()
            self._refresh_preview()

    def mark_start(self) -> None:
        """Mark selection start line."""
        self.selection_start = self.cursor_line
        if self.selection_end is not None and self.selection_end < self.selection_start:
            self.selection_end = None
        self._refresh_preview()

    def mark_end(self) -> None:
        """Mark selection end line."""
        if self.selection_start is None:
            self.selection_start = self.cursor_line
        self.selection_end = self.cursor_line
        self._refresh_preview()

    def append_selection_to_context(self) -> None:
        """Append selected range to the next KI request."""
        if self.file_path is None or not self.lines:
            return

        start = self.selection_start if self.selection_start is not None else self.cursor_line
        end = self.selection_end if self.selection_end is not None else self.cursor_line
        start, end = sorted((start, end))
        selected_lines = self.lines[start:end + 1]
        self.parent_app.append_preview_selection(self.file_path, start + 1, end + 1, selected_lines)

    def _ensure_cursor_visible(self) -> None:
        if self.cursor_line < self.preview_scroll_offset:
            self.preview_scroll_offset = self.cursor_line
        elif self.cursor_line >= self.preview_scroll_offset + self.page_size:
            self.preview_scroll_offset = self.cursor_line - self.page_size + 1

    def _refresh_preview(self) -> None:
        if self.file_path is None:
            self.update("No file selected")
            return

        start = self.preview_scroll_offset
        end = min(len(self.lines), start + self.page_size)
        rendered = [f"{self.file_path.name}", "─" * 60]
        selection_range = None
        if self.selection_start is not None:
            selection_end = self.selection_end if self.selection_end is not None else self.selection_start
            selection_range = range(min(self.selection_start, selection_end), max(self.selection_start, selection_end) + 1)

        for line_no in range(start, end):
            cursor = ">" if line_no == self.cursor_line else " "
            marker = "* " if selection_range and line_no in selection_range else "  "
            rendered.append(f"{cursor}{marker}{line_no + 1:3} {self.lines[line_no]}")

        if end < len(self.lines):
            rendered.append("... (truncated)")

        self.update("\n".join(rendered))
