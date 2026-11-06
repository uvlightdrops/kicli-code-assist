"""
TUI Configuration System

Loads and validates TUI configuration from YAML.
Supports enabling/disabling modules at runtime.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml
from pydantic import BaseModel, Field, validator


class FileTreeConfig(BaseModel):
    """File tree widget configuration."""
    enabled: bool = True
    project_root: str = "."
    ignore_patterns: List[str] = Field(
        default_factory=lambda: [".git", "__pycache__", ".venv", "node_modules"]
    )
    max_depth: int = 10

    class Config:
        extra = "allow"  # Allow additional fields


class AgentTabsConfig(BaseModel):
    """Agent tabs panel configuration."""
    enabled: bool = True
    enabled_tabs: List[str] = Field(
        default_factory=lambda: ["Explain", "Suggest", "Reason", "Metrics"]
    )
    default_tab: str = "Explain"

    class Config:
        extra = "allow"


class LogsPanelConfig(BaseModel):
    """Logs panel configuration."""
    enabled: bool = True
    max_lines: int = 100
    level: str = "INFO"

    class Config:
        extra = "allow"


class ChatPanelConfig(BaseModel):
    """Chat panel configuration."""
    enabled: bool = False
    max_history: int = 50

    class Config:
        extra = "allow"


class PreviewPanelConfig(BaseModel):
    """Preview panel configuration."""
    enabled: bool = True
    max_file_size_mb: int = 1  # Max 1MB for display
    syntax_highlighting: bool = True

    class Config:
        extra = "allow"


class BackendConfig(BaseModel):
    """Backend API configuration."""
    url: str = "http://localhost:8000"
    timeout: int = 30
    retry_count: int = 3
    ws_url: Optional[str] = None  # Auto-derived if None

    @validator("ws_url", pre=True, always=True)
    def derive_ws_url(cls, v, values):
        if v is None and "url" in values:
            http_url = values["url"]
            v = http_url.replace("http://", "ws://").replace("https://", "wss://")
        return v

    class Config:
        extra = "allow"


class StreamingConfig(BaseModel):
    """Streaming configuration (Phase 1.2)."""
    enabled: bool = True
    protocol: str = "websocket"  # websocket | http
    fallback_to_http: bool = True
    min_token_delay_ms: int = 20
    max_buffer_size: int = 100
    auto_reconnect: bool = True
    reconnect_delay_ms: int = 1000
    max_reconnect_attempts: int = 5

    class Config:
        extra = "allow"


class TUIConfig(BaseModel):
    """Main TUI configuration."""
    file_tree: FileTreeConfig = Field(default_factory=FileTreeConfig)
    agent_tabs: AgentTabsConfig = Field(default_factory=AgentTabsConfig)
    preview: PreviewPanelConfig = Field(default_factory=PreviewPanelConfig)
    logs: LogsPanelConfig = Field(default_factory=LogsPanelConfig)
    chat: ChatPanelConfig = Field(default_factory=ChatPanelConfig)
    backend: BackendConfig = Field(default_factory=BackendConfig)
    streaming: 'StreamingConfig' = Field(default_factory=lambda: StreamingConfig())
    
    # Editor modes
    vi_mode: bool = True
    preview_modal: bool = True
    
    # UI
    theme: str = "dark"
    layout: str = "split"  # split | focused
    debug: bool = False

    class Config:
        extra = "allow"


class ConfigLoader:
    """Load and validate TUI configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or self._find_config())
        self.config: TUIConfig = self._load()
    
    def _find_config(self) -> Path:
        """Find config file in standard locations."""
        candidates = [
            Path("config/tui_config.yaml"),
            Path("kicli_code_assist/config/tui_config.yaml"),
            Path.home() / ".kicli" / "tui_config.yaml",
        ]
        
        for path in candidates:
            if path.exists():
                return path
        
        # Return default location (will be created if needed)
        return Path("config/tui_config.yaml")
    
    def _load(self) -> TUIConfig:
        """Load config from YAML file.
        
        Supports both formats:
        1. Top-level sections (new, yaml-cfg-wizard compatible)
        2. Nested under 'tui:' (legacy)
        """
        if not self.config_path.exists():
            # Return defaults
            return TUIConfig()
        
        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f)
            
            if not data:
                return TUIConfig()
            
            # Check if nested under 'tui:' (legacy) or top-level (new)
            if "tui" in data:
                # Legacy format
                tui_data = data.get("tui", {})
            else:
                # New format (top-level sections)
                tui_data = data
            
            return TUIConfig(
                file_tree=FileTreeConfig(**tui_data.get("file_tree", {})),
                agent_tabs=AgentTabsConfig(**tui_data.get("agent_tabs", {})),
                preview=PreviewPanelConfig(**tui_data.get("preview", {})),
                logs=LogsPanelConfig(**tui_data.get("logs", {})),
                chat=ChatPanelConfig(**tui_data.get("chat", {})),
                backend=BackendConfig(**tui_data.get("backend", {})),
                vi_mode=tui_data.get("vi_mode", True),
                preview_modal=tui_data.get("preview_modal", True),
                theme=tui_data.get("theme", "dark"),
                layout=tui_data.get("layout", "split"),
                debug=tui_data.get("debug", False),
            )
        
        except Exception as e:
            print(f"⚠️  Error loading config from {self.config_path}: {e}")
            return TUIConfig()
    
    def save(self, output_path: Optional[str] = None) -> None:
        """Save current config to YAML file."""
        path = Path(output_path or self.config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(
                {"tui": self.config.dict()},
                f,
                default_flow_style=False,
                sort_keys=False,
            )
        
        print(f"✅ Config saved to {path}")
    
    def is_enabled(self, panel: str) -> bool:
        """Check if a panel is enabled."""
        panels = {
            "file_tree": self.config.file_tree.enabled,
            "agent_tabs": self.config.agent_tabs.enabled,
            "preview": self.config.preview.enabled,
            "logs": self.config.logs.enabled,
            "chat": self.config.chat.enabled,
        }
        return panels.get(panel, False)
    
    def get_enabled_panels(self) -> List[str]:
        """Get list of enabled panel names."""
        return [p for p in ["file_tree", "preview", "agent_tabs", "logs", "chat"] if self.is_enabled(p)]
    
    def debug_print(self) -> None:
        """Print current configuration for debugging."""
        print("\n📋 TUI Configuration:")
        print(f"  Backend URL: {self.config.backend.url}")
        print(f"  VI Mode: {self.config.vi_mode}")
        print(f"  Theme: {self.config.theme}")
        print(f"\n  Enabled Panels:")
        for panel in self.get_enabled_panels():
            print(f"    ✅ {panel}")
        print()


# Global config instance
_config: Optional[TUIConfig] = None


def get_config(config_path: Optional[str] = None) -> TUIConfig:
    """Get or create global TUI config."""
    global _config
    if _config is None:
        loader = ConfigLoader(config_path)
        _config = loader.config
    return _config


def load_config(config_path: str) -> TUIConfig:
    """Load config from specific path."""
    global _config
    loader = ConfigLoader(config_path)
    _config = loader.config
    return _config
