"""App-specific configuration accessor for kicli-code-assist.

ki-core deliberately no longer exposes a fat, cross-app config dataclass
(see ki_core.load_config()). Instead, each app owns a thin, typed
accessor for the settings *it* actually needs. This module is
kicli-code-assist's accessor: it wraps the generic, schema-validated
dict returned by ki_core.load_config() and exposes the LLM provider,
storage, context, diff, and security/prompts settings this app owns as
plain attributes.

All defaults come from the merged schema (ki-core's base schema +
kicli-code-assist/schema/kicli.schema.yaml) - there are no hardcoded
fallback values here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from ki_core import ConfigDict, load_config


@dataclass
class AppConfig:
    """Resolved kicli-code-assist configuration."""

    # LLM providers (ki-core base schema: llm.providers.*)
    ki_base_url: str = ""
    ki_api_key: str = ""
    ki_model: str = ""
    ki_endpoint: Optional[str] = None

    ollama_base_url: str = ""
    ollama_model: str = ""

    openai_api_key: str = ""
    openai_model: str = ""
    openai_base_url: str = ""

    # HTTP (ki-core base schema: http.*)
    request_timeout: int = 30
    http_verify_ssl: bool = True

    # Storage (apps' own schema: storage.*)
    kicli_cache_dir: str = ""
    kicli_session_dir: str = ""
    kicli_chat_history_dir: str = ""
    kicli_allowed_base_path: str = ""

    # Context selection (apps.kicli.context.*)
    context_max_files: int = 10
    context_max_size_mb: float = 5
    context_relevance_threshold: float = 0.15
    context_cache_enabled: bool = True
    context_cache_ttl_hours: int = 24
    context_cache_max_size_mb: float = 50
    context_ignore_patterns: str = "__pycache__,*.pyc,node_modules,.git,.env"

    # Diff generation (apps.kicli.diff.*)
    diff_context_lines: int = 3
    diff_format: str = "unified"
    diff_highlight_syntax: bool = True
    diff_auto_apply_threshold: float = 0.8
    diff_max_file_size_kb: int = 100

    # The full resolved config dict, for consumers (e.g. PromptManager,
    # security.py helpers) that need direct access to raw sections
    # (prompts.*, security.*) rather than a flattened attribute.
    raw: ConfigDict = field(default_factory=ConfigDict)

    @classmethod
    def from_yaml(cls, path: Optional[Union[str, Path]] = None) -> "AppConfig":
        """Load and resolve config from YAML + environment variables."""
        payload = load_config(path)

        providers = payload.get_path("llm.providers", {}) or {}
        ki_cfg = providers.get("ki", {}) or {}
        ollama_cfg = providers.get("ollama", {}) or {}
        openai_cfg = providers.get("openai", {}) or {}

        return cls(
            ki_base_url=ki_cfg.get("base_url", ""),
            ki_api_key=ki_cfg.get("api_key", ""),
            ki_model=ki_cfg.get("model", ""),
            ki_endpoint=ki_cfg.get("endpoint") or None,
            ollama_base_url=ollama_cfg.get("base_url", ""),
            ollama_model=ollama_cfg.get("model", ""),
            openai_api_key=openai_cfg.get("api_key", ""),
            openai_model=openai_cfg.get("model", ""),
            openai_base_url=openai_cfg.get("base_url", ""),
            request_timeout=payload.get_path("http.request_timeout", 30),
            http_verify_ssl=payload.get_path("http.verify_ssl", True),
            kicli_cache_dir=payload.get_path("storage.cache_dir", ""),
            kicli_session_dir=payload.get_path("storage.session_dir", ""),
            kicli_chat_history_dir=(
                payload.get_path("apps.kicli.prompt_history_dir")
                or payload.get_path("storage.history_dir", "")
            ),
            kicli_allowed_base_path=payload.get_path("apps.kicli.workspace_root", ""),
            context_max_files=payload.get_path("apps.kicli.context.max_files", 10),
            context_max_size_mb=payload.get_path("apps.kicli.context.max_size_mb", 5),
            context_relevance_threshold=payload.get_path(
                "apps.kicli.context.relevance_threshold", 0.15
            ),
            context_cache_enabled=payload.get_path("apps.kicli.context.cache_enabled", True),
            context_cache_ttl_hours=payload.get_path("apps.kicli.context.cache_ttl_hours", 24),
            context_cache_max_size_mb=payload.get_path(
                "apps.kicli.context.cache_max_size_mb", 50
            ),
            context_ignore_patterns=payload.get_path(
                "apps.kicli.context.ignore_patterns",
                "__pycache__,*.pyc,node_modules,.git,.env",
            ),
            diff_context_lines=payload.get_path("apps.kicli.diff.context_lines", 3),
            diff_format=payload.get_path("apps.kicli.diff.format", "unified"),
            diff_highlight_syntax=payload.get_path("apps.kicli.diff.highlight_syntax", True),
            diff_auto_apply_threshold=payload.get_path(
                "apps.kicli.diff.auto_apply_threshold", 0.8
            ),
            diff_max_file_size_kb=payload.get_path("apps.kicli.diff.max_file_size_kb", 100),
            raw=payload,
        )

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load config from environment variables (KI_CFG_* prefix) plus any discovered YAML."""
        return cls.from_yaml(None)
