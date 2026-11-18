# AutoCommitDetector - Quick Reference

## Import

```python
from kicli_code_assist.auto_commit_detector import AutoCommitDetector
```

## Initialisierung

```python
# Minimal
detector = AutoCommitDetector()

# Mit Optionen
detector = AutoCommitDetector(
    repo_path=Path.cwd(),
    min_commit_interval_minutes=15,
    min_change_lines=50,
)
```

## Methoden

### should_commit() → bool

Prüft, ob Commit empfohlen wird.

```python
if detector.should_commit():
    print("✅ Commit wird empfohlen")
else:
    print("⏭️  Commit nicht empfohlen")
```

### auto_commit() → Optional[str]

Führt Commit durch oder gibt None zurück.

```python
sha = detector.auto_commit()
if sha:
    print(f"✅ Committed: {sha[:8]}")
else:
    print("❌ Kein Commit")
```

## Heuristiken (alle müssen erfüllt sein)

| # | Heuristik | Prüfung | ❌ Wenn |
|---|-----------|---------|--------|
| 1 | Änderungen existieren | `git status` | Keine Dateien geändert |
| 2 | Genug Zeit seit letztem Commit | `git log` vs Zeit | < 15 Min her |
| 3 | Keine unstaged Changes | `git diff` | Manche Dateien nicht gestaged |
| 4 | Keine Secret-Dateien | Regex auf `.env`, `.key` | .env, secrets.* etc staged |
| 5 | Keine laufenden Checks | `pgrep pytest` | Tests/Lints laufen noch |
| 6 | Genug große Changes | Zeile-Anzahl + Type | < 50 Zeilen + chore-Type |

## Commit-Message-Format

```
type(scope): subject
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

**Types:** `fix` `feat` `ui` `docs` `test` `refactor` `perf` `chore`

## Typische Szenarien

### Scenario 1: Einfacher Commit

```python
detector = AutoCommitDetector()
sha = detector.auto_commit()
print(f"Result: {sha or 'No commit'}")
```

### Scenario 2: In Agent-Loop

```python
detector = AutoCommitDetector(min_commit_interval_minutes=30)
for i in range(10):
    # Agent macht Arbeit...
    sha = detector.auto_commit()
    print(f"Iter {i}: {sha[:8] if sha else 'skip'}")
```

### Scenario 3: Mit Error-Handling

```python
try:
    sha = detector.auto_commit()
except Exception as e:
    logger.error(f"Commit failed: {e}")
```

## Troubleshooting

| Problem | Grund | Lösung |
|---------|-------|--------|
| `reason=no_changes` | Nichts geändert | `git status` |
| `reason=unstaged_changes_exist` | Nicht alles gestaged | `git add .` |
| `reason=gitignore_violations` | Secret-Dateien gestaged | `git rm --cached .env` |
| `reason=checks_running` | Tests laufen noch | Warten oder `pytest` stoppen |
| `reason=last_commit_too_recent` | Zu wenig Zeit seit letztem Commit | Warten oder `min_commit_interval_minutes=0` |
| `reason=insufficient_changes_or_keywords` | Zu kleine Changes ohne Keyword | Mehr Code schreiben oder `type=feat` statt `chore` |

## Tests

```bash
# Alle Tests
pytest tests/test_auto_commit_detector.py -v

# Nur Unit-Tests (30)
pytest tests/test_auto_commit_detector.py::TestAutoCommitDetectorUnit -v

# Nur Integration-Tests (6)
pytest tests/test_auto_commit_detector.py::TestAutoCommitDetectorIntegration -v
```

**Test Status:** ✅ 36/36 passed

## Logging

Logger name: `kicli_code_assist.auto_commit_detector`

```python
import logging
logging.basicConfig(level=logging.INFO)
# → Sieht INFO/WARNING/ERROR logs
```

## Häufige Fragen

**F: Kann ich verschiedene Heuristiken deaktivieren?**  
A: Nein, alle 6 müssen erfüllt sein. Nutze `should_commit()` für Custom-Logik.

**F: Wie ändere ich den Commit-Message-Typ?**  
A: Der Typ wird automatisch erkannt aus Diff/Dateinamen. Für Custom: Override `_detect_commit_type()`.

**F: Kann ich Commits in bestimmte Branches blockieren?**  
A: Nein eingebaut. Ergänze Custom-Check in `should_commit()` bevor `auto_commit()` aufrufst.

**F: Wie oft sollte ich `auto_commit()` aufrufen?**  
A: Je nach Use-Case:
- **Tests/Lints:** Alle 5 Minuten
- **Autonome Agenten:** Alle 30-60 Minuten
- **CI/CD:** Nach Workflow-Schritten

**F: Was wenn `auto_commit()` fehlschlägt?**  
A: Prüfe Logs (WARNING/ERROR) und führe `git status` manuell aus.
