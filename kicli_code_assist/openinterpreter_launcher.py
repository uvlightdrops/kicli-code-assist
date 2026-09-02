#!/usr/bin/env python3
"""OpenInterpreter launcher with YAML config."""
import sys
import os
from pathlib import Path
import yaml

# Inject truststore for SSL certificate handling
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from interpreter import interpreter

def find_file(name):
    """Search for config file in standard locations."""
    search_paths = [
        Path.cwd() / name,
        Path.cwd() / "config" / name,
        Path.home() / ".config" / "kicli" / name,
    ]
    for path in search_paths:
        if path.exists():
            return path
    return None

def load_config():
    """Load configuration from YAML files."""
    profile_path = find_file("kicli.yaml")
    creds_path = find_file("creds.yaml")
    
    ki_creds = {}
    ki_profile = {}
    
    if creds_path:
        with creds_path.open() as f:
            creds_yaml = yaml.safe_load(f) or {}
        ki_creds = creds_yaml.get("ki", {}) if isinstance(creds_yaml.get("ki"), dict) else {}
    
    if profile_path:
        with profile_path.open() as f:
            profile_yaml = yaml.safe_load(f) or {}
        ki_profile = profile_yaml.get("ki", {}) if isinstance(profile_yaml.get("ki"), dict) else {}
    
    return ki_creds, ki_profile

# Parse arguments
auto_run = "-y" in sys.argv
if auto_run:
    sys.argv.remove("-y")

# Load config
ki_creds, ki_profile = load_config()

# Configure interpreter
model = ki_profile.get("model", "gpt-4o-mini")
api_key = ki_creds.get("api_key")
api_base = ki_creds.get("base_url", "https://api.openai.com/v1")

print(f"✓ OpenInterpreter Configuration:")
print(f"  Base URL: {api_base}")
print(f"  Model: {model}\n")

# Use custom headers for company auth (x-api-key instead of Authorization: Bearer)
interpreter.llm.model = model
interpreter.llm.api_key = "dummy"  # Placeholder
interpreter.llm.api_base = api_base
interpreter.llm.default_headers = {"x-api-key": api_key}
interpreter.auto_run = auto_run

# Start interactive session
interpreter.chat()








