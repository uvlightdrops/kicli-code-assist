# Stack Configurations

Deploy-Konfigurationen für unterschiedliche Szenarien.

## Files

| Datei | Variante | Use-Case |
|-------|----------|----------|
| **stack.yaml** | #3 Production | **DEFAULT für Semi-Prod** |
| stack-minimal.yaml | #1 Minimal | TUI-only, keine WebUI |
| stack-dev.yaml | #2 Development | Local dev mit HMR |
| stack-semiprod.yaml | #3 Production | Semi-Prod (copy of stack.yaml) |
| stack-full.yaml | #4 Full Stack | Mit DB (Chat-History, später) |

## Quick Start

### Semi-Prod (Production)
```bash
# 1. Frontend bauen
cd web/frontend
npm install
npm run build

# 2. Stack starten (verwendet stack.yaml)
cd /path/to/kicli-code-assist
stackctl -t local start
```

### Local Development (HMR)
```bash
# Frontend npm install (einmalig)
cd web/frontend && npm install

# Stack mit Dev-Variante (von projekt-root)
cd /path/to/kicli-code-assist
# NOTE: stackctl sucht automatisch das aktuelle Projekt
# Bei mehreren Specs: manuell stack.yaml durch stack-dev.yaml ersetzen
stackctl -t local start

# Browser: http://localhost:5173 (React HMR)
# API: http://localhost:8000
```

### TUI Only (keine WebUI)
```bash
# Nutze stack-minimal.yaml statt default stack.yaml
cd /path/to/kicli-code-assist
cp deploy/stack-minimal.yaml deploy/stack.yaml
stackctl -t local start
```

### Mit Database (Zukunft)
```bash
# Nutze stack-full.yaml statt default stack.yaml
cd /path/to/kicli-code-assist
cp deploy/stack-full.yaml deploy/stack.yaml
stackctl -t local start
```

## How stackctl finds spec

stackctl liest `pyproject.toml`:
```toml
[tool.stackctl]
spec_file = "deploy/stack.yaml"  # Default Spec
```

`stack.yaml` ist ein **Symlink** → momentan auf `stack-semiprod.yaml`

Um andere Varianten zu nutzen:
```bash
# Für Dev (HMR):
cd deploy && ln -sf stack-dev.yaml stack.yaml && cd ..
stackctl -t local start

# Für TUI-only:
cd deploy && ln -sf stack-minimal.yaml stack.yaml && cd ..
stackctl -t local start

# Zurück zu Production:
cd deploy && ln -sf stack-semiprod.yaml stack.yaml && cd ..
stackctl -t local start
```

**Hinweis:** Es gibt kein `--spec-file` Flag in stackctl CLI. Der Symlink ermöglicht flexibles Wechseln zwischen Varianten.

## Details

Siehe: `doc/deployment/STACK_YAML_VARIANTS.md`
