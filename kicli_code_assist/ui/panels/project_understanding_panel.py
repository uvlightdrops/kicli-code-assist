"""Project Understanding Display Panel for TUI.

Displays comprehensive project analysis results including:
- Synthesis report
- Architecture metrics
- Key abstractions
- Patterns detected
"""

from textual.widgets import Static
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button
from textual.binding import Binding
import logging

logger = logging.getLogger(__name__)


class ProjectUnderstandingPanel(Static):
    """Panel displaying project understanding analysis results."""

    DEFAULT_CSS = """
    ProjectUnderstandingPanel {
        background: $surface;
        color: $text;
        border: solid $primary;
        height: 1fr;
        width: 1fr;
    }

    ProjectUnderstandingPanel > Vertical {
        width: 1fr;
        height: 1fr;
    }

    ProjectUnderstandingPanel Label {
        margin: 1 1;
    }

    ProjectUnderstandingPanel Button {
        margin: 1 1;
    }

    #understanding-content {
        width: 1fr;
        height: 1fr;
        background: $panel;
        color: $text;
        border: none;
        padding: 1;
        overflow: auto;
    }

    #understanding-header {
        background: $primary;
        color: $text;
        padding: 0 1;
        height: auto;
    }

    #understanding-footer {
        background: $panel;
        color: $text;
        height: auto;
        padding: 1;
    }
    """

    def __init__(self):
        """Initialize project understanding panel."""
        super().__init__()
        self.understanding_data = None
        self.is_loading = False

    def render(self) -> str:
        """Render the panel content."""
        if self.is_loading:
            return """
⠋ Analyzing project...

This may take a moment. Please wait.
Scanning code structure, dependencies, and patterns...
            """

        if not self.understanding_data:
            return """
📊 Project Understanding

Select a project folder and press Ctrl+U to analyze.

This feature provides comprehensive insights:
- Architecture and design patterns
- Code structure and dependencies
- Key abstractions and modules
- Complexity metrics
- Recommendations for improvements

The analysis runs a 5-stage pipeline:
1. Discovery (docs & project metadata)
2. Code Analysis (AST structure extraction)
3. Aggregation (contextual synthesis)
4. LLM Analysis (insight preparation)
5. Synthesis (unified understanding report)
            """

        # Display understanding results
        data = self.understanding_data
        parts = []

        parts.append("=" * 60)
        parts.append(f"📊 {data.get('project_name', 'Project')} - Understanding Analysis")
        parts.append("=" * 60)
        parts.append("")

        # Synthesis report
        if data.get("synthesis_report"):
            report = data["synthesis_report"]
            # Truncate to ~3000 chars for display
            if len(report) > 3000:
                report = report[:3000] + "\n\n[... Report truncated for display. Use Ctrl+E to export full report ...]"
            parts.append(report)
        else:
            parts.append("No synthesis report available.")

        parts.append("")
        parts.append("=" * 60)

        # Metrics footer
        if data.get("metrics"):
            metrics = data["metrics"]
            parts.append("📈 Metrics:")
            parts.append(f"  Modules: {metrics.get('total_modules', 0)}")
            parts.append(f"  LOC: {metrics.get('total_loc', 0)}")
            parts.append(f"  Dependencies: {metrics.get('external_dependencies', 0)}")
            parts.append(f"  Patterns: {', '.join(metrics.get('patterns', []))}")

        return "\n".join(parts)

    def set_understanding_data(self, data: dict) -> None:
        """Update with understanding analysis results."""
        self.understanding_data = data
        self.is_loading = False
        self.refresh()

    def set_loading(self, loading: bool) -> None:
        """Update loading state."""
        self.is_loading = loading
        self.refresh()

    def export_full_report(self) -> str:
        """Get full synthesis report for export."""
        if self.understanding_data:
            return self.understanding_data.get("synthesis_report", "")
        return ""

    def get_aggregated_context(self) -> str:
        """Get aggregated analysis context."""
        if self.understanding_data:
            return self.understanding_data.get("aggregated_context", "")
        return ""
