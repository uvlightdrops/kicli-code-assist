# Diff Engine & Code Edit Features - Benutzerhandbuch

## Überblick

Das Diff Engine System ermöglicht es:
1. **LLM-Output analysieren** → Code-Blöcke extrahieren
2. **Diffs generieren** → Unterschiede visualisieren
3. **Auto-Apply entscheiden** → Basierend auf Confidence Score
4. **Code anwenden** → Patches auf Dateien auftragen

## API-Referenz

### 1. Diffs aus LLM-Output generieren

```python
from kicli_code_assist.context.diff_engine import LLMOutputParser, DiffGenerator
from ki_core import Config

# Konfiguration laden
config = Config.from_env()

# LLM-Output mit Code-Blöcken
llm_output = """
Here's the updated authentication module:

```python
# src/auth.py
def login(username, password):
    # New implementation
    return verify_credentials(username, password)
```

And update the config file:

```yaml
# config.yaml
auth:
  timeout: 30
  retry: 3
```
"""

# Code-Blöcke extrahieren
parser = LLMOutputParser()
code_blocks = parser.parse_code_with_path(llm_output)
# Returns: [("src/auth.py", "python", "def login..."), ("config.yaml", "yaml", "auth:...")]

# Diffs generieren
generator = DiffGenerator()
files = {}
for path, lang, code in code_blocks:
    # Alte Version laden oder leer wenn neu
    old_content = read_file(path) if path_exists(path) else ""
    files[path] = (old_content, code)

diffs = generator.generate_diffs(files)
# Returns: [FileDiff(path, old, new, is_new, changes), ...]
```

### 2. Diff-Details anschauen

```python
# Ein einzelnes Diff
diff = diffs[0]

# Datei-Info
print(f"File: {diff.file_path}")
print(f"New file: {diff.is_new}")
print(f"Deleted: {diff.is_deleted}")
print(f"Similarity: {diff.similarity:.0%}")

# Änderungen analysieren
changes = diff.get_changes()
for change in changes:
    if change.type == "added":
        print(f"+ {change.line_number}: {change.content}")
    elif change.type == "removed":
        print(f"- {change.line_number}: {change.content}")
    else:
        print(f"  {change.line_number}: {change.content}")

# Statistik
stats = diff.count_changes()
print(f"Added: {stats['added']}, Removed: {stats['removed']}")

# Unified Diff (Git-Format)
unified = diff.to_unified_diff(context_lines=3)
print(unified)
```

### 3. Auto-Apply Entscheidung

```python
# Sollte das Diff automatisch angewendet werden?
confidence = parser.estimate_confidence(llm_output)
# confidence: 0.0 - 1.0 (0=niedrig, 1=hoch)

should_apply = generator.should_auto_apply(diff)
# Prüft: similarity > diff_auto_apply_threshold (default 0.75)

if should_apply:
    print(f"✅ Auto-Apply (confidence: {confidence:.0%})")
else:
    print(f"⚠️  Review required (confidence: {confidence:.0%})")
```

### 4. Diff auf Datei anwenden

```python
# Einfache Anwendung (Text-basiert)
result = diff.apply_diff()
if result.success:
    # Neue Datei-Version
    new_content = result.patched_content
    write_file(diff.file_path, new_content)
    print(f"✅ Applied {diff.file_path}")
else:
    print(f"❌ Failed: {result.error}")

# Für größere Projekte: git apply
import subprocess
for diff in diffs:
    unified = diff.to_unified_diff()
    try:
        subprocess.run(
            ["git", "apply"],
            input=unified.encode(),
            check=True,
            cwd="/path/to/repo"
        )
    except subprocess.CalledProcessError as e:
        print(f"Merge conflict in {diff.file_path}")
```

## Konfiguration

Alle Diff-Features werden via `Config` kontrolliert:

```yaml
# ki.yaml
diff:
  context_lines: 3           # Kontext-Zeilen um Änderungen
  format: unified            # unified|side-by-side|inline
  highlight_syntax: true     # Syntax-Highlighting in UI
  auto_apply_threshold: 0.75 # Min. Confidence für Auto-Apply
  max_file_size_kb: 1000     # Größe-Limit für Diffs
```

Oder via Umgebungsvariablen:

```bash
export DIFF_CONTEXT_LINES=3
export DIFF_AUTO_APPLY_THRESHOLD=0.75
export DIFF_FORMAT=unified
```

## Integration in TUI

### 1. Diff-View Widget

```python
from textual.widgets import Static
from textual.containers import Container

class DiffViewer(Static):
    """Unified diff viewer."""
    
    def render_diff(self, diff: FileDiff):
        """Display diff with syntax highlighting."""
        unified = diff.to_unified_diff()
        # Format + highlight für Textual
        self.update(unified)

class DiffPanel(Container):
    """Full diff panel mit controls."""
    
    def __init__(self, diffs: List[FileDiff]):
        self.diffs = diffs
        self.current_idx = 0
    
    def on_key(self, event):
        if event.key == "j":  # Next diff
            self.current_idx = min(self.current_idx + 1, len(self.diffs) - 1)
            self.refresh_view()
        elif event.key == "k":  # Prev diff
            self.current_idx = max(self.current_idx - 1, 0)
            self.refresh_view()
        elif event.key == "a":  # Apply this diff
            self.apply_current_diff()
        elif event.key == "A":  # Apply all
            self.apply_all_diffs()
```

### 2. Chat Integration

```python
# In chat_ui.py (TUI)

# Nach LLM-Response:
if "```" in llm_response:  # Code-Blöcke erkannt?
    
    # 1. Diffs generieren
    diffs = generate_diffs_from_response(llm_response)
    
    # 2. Status anzeigen
    status = f"📝 {len(diffs)} files | Confidence: {confidence:.0%}"
    self.status_bar.update(status)
    
    # 3. Diff-Viewer öffnen (Ctrl+D)
    self.show_diff_viewer(diffs)
    
    # 4. Auto-Apply wenn sicher genug
    if confidence > threshold:
        self.apply_diffs_automatically(diffs)
```

### 3. Keyboard Shortcuts

| Shortcut | Aktion |
|----------|--------|
| `Ctrl+D` | Diff-Viewer öffnen |
| `j` / `k` | Nächstes/Vorheriges Diff |
| `a` | Aktuelles Diff anwenden |
| `A` | Alle Diffs anwenden |
| `r` | Diff ablehnen |
| `R` | Alle Diffs ablehnen |
| `Ctrl+F` | Focus File Preview |
| `Ctrl+B` | Focus Browser |
| `Ctrl+C` | Focus Chat |
| `Ctrl+I` | Focus Input |
| `q` | Diff-Viewer schließen |

## Workflows

### Workflow 1: Review & Approve

```
User:  "Add error handling to login function"
   ↓
LLM:   "```python\ndef login():\n    try: ..."
   ↓
TUI:   [Ctrl+D] → Shows diff
   ↓
User:  Reviews changes [j/k to navigate]
   ↓
User:  [a] to apply → "✅ Applied src/auth.py"
   ↓
Chat:  "Changes applied! Commit message: ..."
```

### Workflow 2: Auto-Apply (High Confidence)

```
User:  "Format Python files"
   ↓
LLM:   Returns code with high confidence
   ↓
TUI:   "⚠️ Confidence 92% | Auto-applying in 3s... [q to cancel]"
   ↓
Files: Updated automatically
   ↓
Chat:  "✅ Applied 4 files | Summary: ..."
```

### Workflow 3: Conflict Resolution

```
User:  "Update config.yaml"
   ↓
LLM:   Returns changes
   ↓
TUI:   [a] to apply → "⚠️ Merge conflict in config.yaml"
   ↓
User:  Manual edit needed
   ↓
Chat:  "Use: git mergetool config.yaml"
```

## Testing

```bash
# Alle Diff-Tests laufen
pytest tests/test_diff_engine.py -v

# Mit Coverage
pytest tests/test_diff_engine.py --cov=kicli_code_assist.context.diff_engine

# Spezifischer Test
pytest tests/test_diff_engine.py::TestDiffGenerator::test_should_auto_apply_high_confidence -v
```

## Debugging

```python
# Verbose output
import logging
logging.basicConfig(level=logging.DEBUG)

# LLM-Output analysieren
parser = LLMOutputParser()
blocks = parser.parse_code_with_path(response)
print(f"Found {len(blocks)} code blocks:")
for path, lang, code in blocks:
    print(f"  {path} ({lang}): {len(code)} chars")

# Diff-Details
for diff in diffs:
    print(f"\n{diff.file_path}:")
    print(f"  Similarity: {diff.similarity}")
    print(f"  Changes: {diff.count_changes()}")
    print(f"  Auto-apply: {generator.should_auto_apply(diff)}")
```

## Tipps für robuste Diffs

1. **Syntax-Validierung**: Stelle sicher, dass LLM-Code valid ist
2. **Größe-Limits**: Nutze `diff_max_file_size_kb` um OOM zu vermeiden
3. **Fallback-Patterns**: Parser versucht mehrere Code-Block-Formate
4. **Manual Review**: Bei Confidence < 70% immer reviewen
5. **Git Integration**: Nutze `git apply` statt direktes Patchen für Merges

## Nächste Schritte

- [ ] Diff Viewer Widget in Textual implementieren
- [ ] Side-by-side view für größere Diffs
- [ ] Syntax-Highlighting (Pygments integration)
- [ ] Undo/Redo für angewendete Diffs
- [ ] Diff History speichern
