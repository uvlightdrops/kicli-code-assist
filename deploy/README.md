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
stackctl local start --project .
```

### Local Development (HMR)
```bash
# Frontend npm install (einmalig)
cd web/frontend && npm install

# Stack mit Dev-Variante
cd /path/to/kicli-code-assist
stackctl local start --project . --spec-file deploy/stack-dev.yaml

# Browser: http://localhost:5173 (React HMR)
# API: http://localhost:8000
```

### TUI Only (keine WebUI)
```bash
stackctl local start --project . --spec-file deploy/stack-minimal.yaml
```

### Mit Database (Zukunft)
```bash
stackctl local start --project . --spec-file deploy/stack-full.yaml
```

## Details

Siehe: `doc/deployment/STACK_YAML_VARIANTS.md`
