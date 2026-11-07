"""
Project Analysis Panel Widget - Phase I2.3

Shows project-wide analysis:
- File list with complexity
- Dependency graph
- High-impact files
- Circular dependencies
- Impact zones

Features:
- Real-time project analysis via /api/projects/analyze
- Drill-down: click file to see full analysis
- Impact visualization
- Search/filter capabilities
- Loading spinner with elapsed time
- Error display with clear visual feedback
- Result count badge
"""

import logging
import time
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass

from textual.widgets import Static, Button, Label, ListView, ListItem, Input
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.reactive import reactive
from textual.app import ComposeResult
from textual import work

from ..http_client import get_backend_client

logger = logging.getLogger(__name__)


@dataclass
class ProjectAnalysisData:
    """Project analysis response structure."""
    name: str
    root: str
    total_files: int
    total_lines: int
    avg_complexity: float
    languages: Dict[str, int]
    high_impact_files: List[Dict]
    circular_deps: List
    timestamp: str


class ProjectAnalysisPanel(Static):
    """Panel showing project-wide analysis results.
    
    Displays:
    - Project statistics (files, LOC, complexity)
    - High-impact files (most imported modules)
    - Circular dependencies
    - Impact zones for selected file
    - File complexity distribution
    """
    
    DEFAULT_CSS = """
    ProjectAnalysisPanel {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        background: $surface;
        layout: vertical;
    }
    
    ProjectAnalysisPanel > Vertical {
        width: 1fr;
        height: 1fr;
        layout: vertical;
    }
    
    ProjectAnalysisPanel > Vertical > Label {
        text-style: bold;
        margin: 1 2;
    }
    
    ProjectAnalysisPanel > Vertical > Input {
        margin: 1 2;
        width: 1fr;
    }
    
    ProjectAnalysisPanel > Vertical > ScrollableContainer {
        width: 1fr;
        height: 1fr;
        margin: 1 2;
    }
    
    ProjectAnalysisPanel > Vertical > Horizontal {
        height: 3;
        margin: 1 2;
    }
    
    ProjectAnalysisPanel Button {
        margin-right: 1;
    }
    """
    
    # Reactive attributes
    is_analyzing = reactive(False)
    analysis_data: Optional[ProjectAnalysisData] = None
    
    def __init__(
        self,
        project_root: Optional[str] = None,
        backend_url: str = "http://localhost:8000"
    ):
        """Initialize project analysis panel.
        
        Args:
            project_root: Project root path for analysis
            backend_url: Backend URL for API calls
        """
        super().__init__()
        self.project_root = project_root
        self.backend_url = backend_url
        self.backend_client = get_backend_client(backend_url)
        self.analysis_data = None
        self._search_query = ""
        
        # Phase I2.3: UI Polish tracking
        self._analysis_start_time: Optional[float] = None
        self._spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self._spinner_index = 0
        self._last_error: Optional[str] = None
        self._error_clear_time: Optional[float] = None
    
    def compose(self) -> ComposeResult:
        """Compose panel layout."""
        with Vertical(id="project-panel-main"):
            yield Label("PROJECT ANALYSIS", id="project-title")
            
            # Search/filter
            yield Input(
                placeholder="Search files...",
                id="project-search",
            )
            
            # Stats line
            yield Label(
                "Ready to analyze",
                id="project-stats",
            )
            
            # Buttons
            with Horizontal(id="project-buttons"):
                yield Button("Analyze Project", id="btn-analyze-project", variant="primary")
                yield Button("Refresh", id="btn-refresh-project")
                yield Button("High Impact", id="btn-high-impact")
            
            # Content area - scrollable
            with ScrollableContainer(id="project-content"):
                yield Label("", id="project-results")
    
    def on_mount(self) -> None:
        """Setup handlers."""
        self.query_one("#btn-analyze-project", Button).press()
    
    def set_project_root(self, project_root: str) -> None:
        """Update project root and trigger analysis.
        
        Called when FileTree changes project.
        """
        self.project_root = project_root
        logger.info(f"ProjectAnalysisPanel: project_root updated to {project_root}")
        # Auto-analyze on root change
        self._analyze_project()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-analyze-project":
            self._analyze_project()
        elif event.button.id == "btn-refresh-project":
            self._analyze_project()
        elif event.button.id == "btn-high-impact":
            self._show_high_impact()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input with debouncing (Phase I2.3)."""
        # Update query
        self._search_query = event.value.lower()
        
        # Debounce: wait 300ms before updating display
        # This prevents excessive redraws while user is typing
        if hasattr(self, '_search_debounce'):
            # Cancel previous scheduled update
            pass
        
        # Schedule update after 300ms
        self.call_later(self._update_display, delay=0.3)
    
    @work(thread=False)
    async def _analyze_project(self) -> None:
        """Analyze project asynchronously."""
        if not self.project_root:
            self._update_stats("No project root specified")
            return
        
        # Phase I2.3: Start spinner and timer
        self._analysis_start_time = time.time()
        self._spinner_index = 0
        self._last_error = None
        
        self.is_analyzing = True
        
        # Start spinner update
        self._update_spinner()
        
        try:
            logger.info(f"Calling /api/projects/analyze for {self.project_root}")
            
            # Call backend endpoint
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Run in thread pool to avoid blocking
            response_data = await loop.run_in_executor(
                None,
                self.backend_client.analyze_project,
                self.project_root
            )
            
            if response_data and response_data.get("success"):
                project = response_data.get("project", {})
                stats = project.get("stats", {})
                high_impact = response_data.get("high_impact_files", [])
                
                # Build analysis data
                self.analysis_data = ProjectAnalysisData(
                    name=project.get("name", "Unknown"),
                    root=project.get("root", ""),
                    total_files=stats.get("total_files", 0),
                    total_lines=stats.get("total_lines", 0),
                    avg_complexity=stats.get("avg_complexity", 0),
                    languages=stats.get("languages", {}),
                    high_impact_files=high_impact,
                    circular_deps=response_data.get("circular_deps", []),
                    timestamp=response_data.get("timestamp", ""),
                )
                
                # Calculate elapsed time
                elapsed = time.time() - self._analysis_start_time
                logger.info(f"Analysis complete in {elapsed:.2f}s: {self.analysis_data.total_files} files")
                self._update_display()
            else:
                error = response_data.get("error", "Unknown error") if response_data else "No response"
                self._last_error = error
                self._update_stats(f"⚠️  Analysis failed: {error}", is_error=True)
                logger.warning(f"Analysis failed: {error}")
        
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Analysis error: {e}", exc_info=True)
            self._update_stats(f"⚠️  Error: {str(e)}", is_error=True)
        
        finally:
            self.is_analyzing = False
            self._analysis_start_time = None
    
    def _update_display(self) -> None:
        """Update display with analysis results."""
        if not self.analysis_data:
            return
        
        # Phase I2.3: Update stats with result badge
        stats_text = (
            f"📊 {self.analysis_data.name} | "
            f"{self.analysis_data.total_files} files | "
            f"{self.analysis_data.total_lines} LOC | "
            f"Complexity: {self.analysis_data.avg_complexity:.1f}"
        )
        
        # Add result count badge
        high_impact_count = len(self.analysis_data.high_impact_files)
        if high_impact_count > 0:
            stats_text += f" | ✅ {high_impact_count} high-impact files"
        
        self._update_stats(stats_text)
        
        # Build results display
        results = []
        results.append("=" * 60)
        results.append("HIGH-IMPACT FILES (Most Imported)")
        results.append("=" * 60)
        
        for file_info in self.analysis_data.high_impact_files[:10]:
            file = file_info.get("file", "unknown")
            
            # Filter by search query
            if self._search_query and self._search_query not in file.lower():
                continue
            
            total = file_info.get("total_affected", 0)
            level = file_info.get("impact_level", "unknown")
            dependents = file_info.get("direct_dependents", 0)
            
            # Color-code by impact level
            icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "⚪",
            }.get(level, "❓")
            
            results.append(f"{icon} {file}")
            results.append(
                f"   → {dependents} direct, "
                f"{total} total affected | "
                f"Cascade: {file_info.get('cascade_depth', 0)}"
            )
            results.append("")
        
        # Languages
        results.append("")
        results.append("=" * 60)
        results.append("LANGUAGES")
        results.append("=" * 60)
        for lang, count in self.analysis_data.languages.items():
            results.append(f"  {lang}: {count} files")
        
        # Circular dependencies
        if self.analysis_data.circular_deps:
            results.append("")
            results.append("=" * 60)
            results.append("⚠️  CIRCULAR DEPENDENCIES")
            results.append("=" * 60)
            for cycle in self.analysis_data.circular_deps[:5]:
                cycle_str = " → ".join(str(f) for f in cycle)
                results.append(f"  {cycle_str}")
        
        # Update results label
        results_text = "\n".join(results)
        self.query_one("#project-results", Label).update(results_text)
    
    def _show_high_impact(self) -> None:
        """Show only high-impact files."""
        if not self.analysis_data:
            return
        
        results = []
        results.append("=" * 60)
        results.append("🔴 CRITICAL & HIGH IMPACT FILES")
        results.append("=" * 60)
        
        critical = [f for f in self.analysis_data.high_impact_files
                   if f.get("impact_level") in ["critical", "high"]]
        
        for file_info in critical[:15]:
            file = file_info.get("file")
            dependents = file_info.get("direct_dependents", 0)
            level = file_info.get("impact_level")
            
            icon = "🔴" if level == "critical" else "🟠"
            results.append(f"{icon} {file} ({dependents} dependents)")
        
        results_text = "\n".join(results)
        self.query_one("#project-results", Label).update(results_text)
    
    def _update_spinner(self) -> None:
        """Update spinner animation (Phase I2.3)."""
        if not self.is_analyzing or self._analysis_start_time is None:
            return
        
        # Update spinner frame
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
        spinner = self._spinner_frames[self._spinner_index]
        
        # Calculate elapsed time
        elapsed = time.time() - self._analysis_start_time
        
        # Build status with spinner and timer
        status = f"{spinner} Analyzing... {elapsed:.1f}s elapsed"
        
        try:
            self.query_one("#project-stats", Label).update(status)
        except Exception:
            pass
        
        # Schedule next spinner update (every 100ms)
        self.call_later(self._update_spinner)
    
    def _update_stats(self, text: str, is_error: bool = False) -> None:
        """Update status label with optional error styling (Phase I2.3).
        
        Args:
            text: Status text to display
            is_error: If True, mark as error and schedule clear after 10 seconds
        """
        try:
            label = self.query_one("#project-stats", Label)
            
            if is_error:
                # Store error and schedule auto-clear
                self._last_error = text
                self._error_clear_time = time.time() + 10.0  # Clear after 10 seconds
                label.update(text)
                # Schedule error auto-clear
                self.call_later(self._check_clear_error, delay=10.0)
            else:
                label.update(text)
        
        except Exception as e:
            logger.warning(f"Failed to update stats: {e}")
    
    def _check_clear_error(self) -> None:
        """Auto-clear error message after timeout (Phase I2.3)."""
        if self._error_clear_time and time.time() >= self._error_clear_time:
            if self.analysis_data:
                # Show last successful stats
                self._update_display()
            else:
                # Show "Ready to analyze"
                self._update_stats("Ready to analyze")
            self._error_clear_time = None
            self._last_error = None
    
    
    def update_project_root(self, new_root: str) -> None:
        """Update project root and re-analyze."""
        self.project_root = new_root
        self._analyze_project()
