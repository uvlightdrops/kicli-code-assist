"""UI components for kicli-code-assist TUI.

Phase 1 (Nov 2026): Modular TUI with inside-out approach.
- tui_client.py: Main Textual application (KICLITUIApp)
- config.py: Configuration system (enable/disable modules via YAML)
- widgets/: Reusable modular components (file tree, tabs, modals, etc.)

Phase 1 Roadmap:
1. Core infrastructure (config system, base app) ✅
2. File browser widget (tree navigation)
3. Preview modal (file preview)
4. VI editor modal (input editing)
5. Agent tabs panel (response display)
6. Input bar + status (submission)
7. Composition (main layout)
8. Backend connectivity (API client)
9. Integration testing + polish
"""

from .tui_client import KICLITUIApp, run_tui
from .config import ConfigLoader, TUIConfig, get_config, load_config

__all__ = [
    "KICLITUIApp",
    "run_tui",
    "ConfigLoader",
    "TUIConfig",
    "get_config",
    "load_config",
]
