# Auto-Commit Detection Agent

## Überblick

Der `AutoCommitDetector` ist ein autonomer Agent, der automatisch entscheidet, ob Änderungen committed werden sollen. Er implementiert intelligente Heuristiken zur Erkennung von commit-würdigen Änderungen und generiert automatisch konventionelle Commit-Nachrichten.

**Hauptmerkmale:**
- 🤖 Autonome Commit-Entscheidung basierend auf 6 Heuristiken
- 📝 Automatische Commit-Message-Generierung (Conventional Commits)
- 🛡️ Sicherheitsprüfungen (kein Leaking von Secrets)
- 📊 Logging für Auditierbarkeit
- ✅ 36 umfassende Tests (Unit + Integration)

---

## Installation

Das Modul ist bereits in `/kicli_code_assist/auto_commit_detector.py` installiert.

```python
from kicli_code_assist.auto_commit_detector import AutoCommitDetector
```

---

## Schnelleinstieg

### Basische Nutzung

```python
from pathlib import Path
from kicli_code_assist.auto_commit_detector import AutoCommitDetector

# Detector initialisieren
detector = AutoCommitDetector(
    repo_path=Path.cwd(),           # Git-Repo Pfad (Standard: cwd)
    min_commit_interval_minutes=15, # Min. Zeit seit letztem Commit
    min_change_lines=50,            # Min. Zeilen für Chore-Commits
)

# Entscheidung treffen
if detector.should_commit():
    print("✅ Commit wird empfohlen")
    sha = detector.auto_commit()
    if sha:
        print(f"✅ Committed: {sha[:8]}")
else:
    print("⏭️  Commit nicht empfohlen (Heuristiken nicht erfüllt)")
```

### In Autonomen Agenten

```python
# Autonomer Agent mit periodischen Commits
detector = AutoCommitDetector(min_commit_interval_minutes=30)

for iteration in range(10):
    # Agent macht Arbeit...
    # (Dateien ändern, Code schreiben, Docs aktualisieren, etc.)
    
    # Am Ende: Auto-Commit versuchen
    sha = detector.auto_commit()
    if sha:
        print(f"Auto-committed: {sha[:8]}")
```

---

## Heuristiken für Commit-Entscheidung

Der Agent nutzt 6 Heuristiken, die alle erfüllt sein müssen:

### 1. ✅ Änderungen existieren
- **Prüfung:** `git status --porcelain`
- **Anforderung:** Mindestens eine geänderte Datei
- **Grund:** Keine leeren Commits

### 2. ✅ Letzter Commit > 15 Minuten her
- **Prüfung:** Vergleich `git log -1 --format=%cI` mit aktuellem Zeitstempel
- **Standard:** 15 Minuten (konfigurierbar)
- **Grund:** Verhindert zu häufige Commits

### 3. ✅ Keine unstaged Changes
- **Prüfung:** `git diff --name-only` (prüft geänderte, nicht stagedDateien)
- **Anforderung:** Alle Changes sind entweder staged ODER tracked und committed
- **Grund:** Konsistenz - nur komplette, bewusste Changes committen

### 4. ✅ Keine .gitignore-Violations
- **Prüfung:** Regex-Matching gegen staged Dateien:
  - `.env`, `.env.local`
  - `secrets.*`, `creds.*`
  - `*.key`, `*.pem`
  - `private.*`
- **Grund:** Verhindert versehentliches Leaking von Secrets

### 5. ✅ Keine laufenden Tests/Lints
- **Prüfung:** `pgrep -f "pytest|mypy|pylint|flake8"`
- **Implementierung:** Filtert aktuelle Prozess und Parent aus
- **Grund:** Commits nur nach erfolgreichem Check

### 6. ✅ Change Size & Semantic Keywords
- **Für Feature-Types** (fix, feat, test, docs): Beliebige Größe OK
- **Für andere** (chore, refactor): Mindestens 50 Zeilen (konfigurierbar)
- **Grund:** Verhindert zu triviale "chore" Commits

---

## Commit-Message-Format

Der Agent generiert automatisch Commit-Messages im Conventional Commits Format:

```
type(scope): subject

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

### Beispiele

```
feat(api): Add new user endpoint
fix(auth): Resolve login token expiration
test(detector): Add integration test coverage
docs(README): Update installation instructions
refactor(utils): Simplify string parsing logic
ui(components): Improve button styling
```

### Type-Erkennung

Der Agent erkennt den Commit-Type automatisch:

| Type | Erkannungskriterium | Beispiel |
|------|-------------------|---------|
| `fix` | "fix" Keyword im Diff | Bugfixes |
| `feat` | "feat" Keyword im Diff | Neue Features |
| `test` | Dateipath enthält `test_` oder `_test.py` | Test-Dateien |
| `docs` | Dateipath `.md`, `.rst`, `.txt` | Dokumentation |
| `ui` | Dateipath enthält `ui/`, `component`, `widget` | UI-Changes |
| `chore` | Standard-Fallback | Alles andere |

### Scope-Erkennung

Der Agent bestimmt den Scope aus der Verzeichnisstruktur:

```
kicli_code_assist/
├── api/              <- Scope: "api"
├── ui/               <- Scope: "ui"
└── utils/            <- Scope: "utils"
```

---

## API-Referenz

### Klasse: `AutoCommitDetector`

#### Constructor

```python
AutoCommitDetector(
    repo_path: Optional[Path] = None,
    min_commit_interval_minutes: int = 15,
    min_change_lines: int = 50,
)
```

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|---------|-------------|
| `repo_path` | Path | CWD | Git-Repository Pfad |
| `min_commit_interval_minutes` | int | 15 | Min. Zeit zwischen Commits |
| `min_change_lines` | int | 50 | Min. Zeilen für Chore-Commits |

#### Öffentliche Methoden

##### `should_commit() -> bool`

Entscheidet, ob ein Commit empfohlen wird.

**Returns:** `True` wenn alle Heuristiken erfüllt, `False` sonst

**Logging:**
- INFO: "Commit criteria met" (wenn ja)
- WARNING: "Skipped commit: reason=..." (wenn nein)

**Beispiel:**
```python
if detector.should_commit():
    print("Commit empfohlen")
else:
    print("Commit nicht empfohlen")
```

##### `auto_commit() -> Optional[str]`

Führt einen Commit aus, wenn `should_commit()` True ist.

**Returns:** 
- Vollständiger Commit-SHA (40 Zeichen) wenn erfolgreich
- `None` wenn Heuristiken nicht erfüllt oder Fehler

**Logging:**
- INFO: "Commit made: SHA=abc123 | Message=..." (erfolgreich)
- WARNING: "Skipped commit: reason=..." (nicht empfohlen)
- ERROR: "Commit failed: ..." (Git-Fehler)

**Beispiel:**
```python
sha = detector.auto_commit()
if sha:
    print(f"Erfolgreich committed: {sha[:8]}")
else:
    print("Commit nicht durchgeführt")
```

---

## Logging

Der Agent logged alle Entscheidungen für Auditierbarkeit.

### Log-Level: INFO

```
Commit made: SHA=abc123def | Message=feat(api): Add new endpoint
```

### Log-Level: WARNING

```
Skipped commit: reason=no_changes
Skipped commit: reason=last_commit_too_recent
Skipped commit: reason=unstaged_changes_exist
Skipped commit: reason=gitignore_violations
Skipped commit: reason=checks_running
Skipped commit: reason=insufficient_changes_or_keywords
```

### Log-Level: ERROR

```
Commit failed: fatal: not a git repository
Unexpected error during commit: FileNotFoundError
```

---

## Tests

Das Modul hat 36 umfangreiche Tests:

### Unit-Tests (30 Tests)

Prüfen einzelne Heuristiken und Funktionen in Isolation.

**Beispiele:**
- `test_should_commit_no_changes()` - Scenario: Keine Changes
- `test_should_commit_unstaged_changes()` - Scenario: Unstaged Changes vorhanden
- `test_detect_commit_type_fix()` - Erkennung: "fix" Type
- `test_generate_subject_max_length()` - Subject-Länge: Max 50 Zeichen
- `test_has_gitignore_violations_secret_files()` - Sicherheit: Secret-Erkennung

### Integration-Tests (6 Tests)

Prüfen komplette Workflows mit echtem Git.

**Beispiele:**
- `test_auto_commit_flow_complete()` - Kompletter Workflow: Modify -> Commit
- `test_auto_commit_no_commit_when_unstaged()` - Unstaged Changes blockieren Commit
- `test_auto_commit_respects_commit_interval()` - Min. Zeit zwischen Commits wird beachtet
- `test_auto_commit_message_format()` - Commit-Message Format korrekt
- `test_auto_commit_multiple_scenarios()` - Mehrere Szenarien hintereinander

### Tests ausführen

```bash
# Alle Tests
pytest tests/test_auto_commit_detector.py -v

# Nur Unit-Tests
pytest tests/test_auto_commit_detector.py::TestAutoCommitDetectorUnit -v

# Nur Integration-Tests
pytest tests/test_auto_commit_detector.py::TestAutoCommitDetectorIntegration -v

# Einzelner Test
pytest tests/test_auto_commit_detector.py::TestAutoCommitDetectorUnit::test_should_commit_all_criteria_met -v
```

---

## Prakteische Beispiele

### Beispiel 1: Einfache Verwendung

```python
from kicli_code_assist.auto_commit_detector import AutoCommitDetector

detector = AutoCommitDetector()

# Prüfen und committen, falls möglich
sha = detector.auto_commit()

if sha:
    print(f"✅ Auto-committed: {sha[:8]}")
else:
    print("⏭️  Kein Commit (Heuristiken nicht erfüllt)")
```

### Beispiel 2: Mit Logging

```python
import logging
from kicli_code_assist.auto_commit_detector import AutoCommitDetector

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)

detector = AutoCommitDetector(min_commit_interval_minutes=5)
sha = detector.auto_commit()

# Output:
# INFO: Commit made: SHA=abc123 | Message=feat(utils): Add helper function
```

### Beispiel 3: In Agent-Loop

```python
from kicli_code_assist.auto_commit_detector import AutoCommitDetector

detector = AutoCommitDetector(min_commit_interval_minutes=30)

class CodeAgent:
    def run_iteration(self):
        # Agent macht Arbeit...
        self.write_code()
        self.update_docs()
        
        # Am Ende: Auto-Commit versuchen
        sha = detector.auto_commit()
        return sha

agent = CodeAgent()
for i in range(10):
    sha = agent.run_iteration()
    if sha:
        print(f"Iteration {i}: Committed {sha[:8]}")
```

### Beispiel 4: Custom Konfiguration

```python
from pathlib import Path
from kicli_code_assist.auto_commit_detector import AutoCommitDetector

# Spezialisierte Konfiguration für Autonomous Agent
detector = AutoCommitDetector(
    repo_path=Path("/path/to/project"),
    min_commit_interval_minutes=60,  # Länger für autonome Agenten
    min_change_lines=100,             # Höhere Anforderung für Chore-Commits
)

# Oder mit Custom Defaults:
class MyAutoCommitAgent(AutoCommitDetector):
    def __init__(self, **kwargs):
        super().__init__(
            min_commit_interval_minutes=45,
            min_change_lines=75,
            **kwargs
        )

agent = MyAutoCommitAgent()
sha = agent.auto_commit()
```

---

## Best Practices

### 1. ✅ Immer Return-Wert prüfen

```python
sha = detector.auto_commit()
if sha:
    # Commit erfolgreich
    logger.info(f"Committed: {sha[:8]}")
else:
    # Kein Commit durchgeführt
    logger.warning("No commit made")
```

### 2. ✅ Passende Interval-Zeit setzen

```python
# Für Tests/Lints: Kürzere Interval
detector = AutoCommitDetector(min_commit_interval_minutes=5)

# Für autonome Agenten: Längere Interval
detector = AutoCommitDetector(min_commit_interval_minutes=60)
```

### 3. ✅ In Try-Except einwickeln

```python
try:
    sha = detector.auto_commit()
except subprocess.CalledProcessError as exc:
    logger.error(f"Git command failed: {exc}")
except Exception as exc:
    logger.error(f"Unexpected error: {exc}")
```

### 4. ✅ Für Agent-Loops nutzen

```python
class AutonomousCodeAgent:
    def __init__(self):
        self.detector = AutoCommitDetector(min_commit_interval_minutes=30)
    
    def run(self):
        for iteration in range(100):
            # Arbeit machen
            self.generate_code()
            
            # Commit versuchen
            self.detector.auto_commit()
```

### 5. ❌ Nicht verwenden für

- **Sensitive Branches** (main, production): Nutze PR-Workflow stattdessen
- **Ohne Logging**: Immer Auditierbarkeit gewährleisten
- **Für Revert/Hotfixes**: Diese brauchen manuellen Review

---

## Troubleshooting

### "Skipped commit: reason=no_changes"

**Problem:** Keine geänderten Dateien

**Lösung:** 
```bash
git status  # Prüfe ob Dateien geändert sind
git add .   # Stage die Dateien
```

### "Skipped commit: reason=unstaged_changes_exist"

**Problem:** Manche Dateien sind nicht gestaged

**Lösung:**
```bash
git add .              # Stage alle Dateien
# ODER
git diff --name-only   # Prüfe welche Dateien unstaged sind
```

### "Skipped commit: reason=gitignore_violations"

**Problem:** Secret-Dateien sind staged (z.B. `.env`)

**Lösung:**
```bash
git rm --cached .env   # Entferne aus Staging
# Oder: Füge zu .gitignore hinzu
```

### "Skipped commit: reason=checks_running"

**Problem:** Tests/Lints laufen noch

**Lösung:**
```bash
pgrep -f "pytest|mypy"  # Prüfe laufende Prozesse
# Warte bis Tests fertig sind
```

### "Skipped commit: reason=last_commit_too_recent"

**Problem:** Letzter Commit ist weniger als 15 Minuten her

**Lösung:**
```python
# Reduziere die Interval:
detector = AutoCommitDetector(min_commit_interval_minutes=0)
```

---

## Dateistruktur

```
kicli-code-assist/
├── kicli_code_assist/
│   └── auto_commit_detector.py          ← Hauptmodul
├── tests/
│   └── test_auto_commit_detector.py      ← 36 Tests (Unit + Integration)
├── examples/
│   └── auto_commit_detector_examples.py  ← Praktische Beispiele
└── doc/
    └── AUTO_COMMIT_DETECTOR.md           ← Diese Dokumentation
```

---

## Lizenz

Siehe LICENSE im Projekt-Root.

---

## Autor

Erstellt für kicli-code-assist mit ❤️ von Copilot.

Letztes Update: 2026-11-17
