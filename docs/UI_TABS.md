# kicli-assist TUI Tabs Guide

Die Terminal UI ist in mehrere Tabs unterteilt. Jeder Tab hat eine spezifische Funktion für den Workflow.

## Tab-Übersicht

### 1. **Logging Tab** ⭐ (Default active)
- **Funktion:** Real-time logs und debugging
- **Inhalt:**
  - **Oben:** Aktives Logfile + Pfad
    ```
    📄 Logfile: /home/flow/.cache/kicli/kicli.log (75.2 KB)
    ```
  - **Filter-Buttons:** ERROR | WARN | INFO | DEBUG | ALL
  - **Logs:** Alle Events chronologisch
    ```
    [2026-10-19 11:25:34] INFO  LLM Query to OpenAI
      Model: gpt-4o-mini
      URL: https://api.openai.com/v1/chat/completions
      Tokens: 234 (est.)
    
    [2026-10-19 11:25:36] DEBUG Hunk creation
      Found 1 code block in response
      Created hunk: file.py:1-10 (5 lines)
    
    [2026-10-19 11:25:37] ERROR All providers exhausted
      Provider: OpenAI
      Error: Invalid API key
    ```
- **Zugriff:** Automatisch aktiv beim Start, oder `Ctrl+1`
- **Wichtig:** Hier sehen wir EXAKT was zur KI geht und was zurückkommt

### 2. **Chat Tab**
- **Funktion:** Interaktion mit KI
- **Inhalt:**
  - Deine Prompts
  - KI-Responses (wenn inline chat enabled)
  - Status-Messages
- **Zugriff:** `Ctrl+2` oder Tab-Navigation

### 3. **Terminal Tab**
- **Funktion:** ???  (aktuell unklar)
- **Inhalt:** 
- **Zugriff:** `Ctrl+3`
- **TODO:** Bitte klären - was ist der Unterschied zu Shell Tab?

### 4. **Shell Tab**
- **Funktion:** ???  (aktuell unklar)
- **Inhalt:** 
- **Zugriff:** `Ctrl+X` oder `Ctrl+4`
- **TODO:** Bitte klären - was ist der Unterschied zu Terminal Tab?

### 5. **File Browser / Editor Tabs**
- **Dynamisch:** Ein Tab pro offener Datei
- **Funktion:** Dateiinhalt anschauen & bearbeiten
- **Zugriff:** `Ctrl+Tab` / `Ctrl+Shift+Tab` zum Wechseln

---

## LLM Query Transparency (Was der Log zeigt)

## Workflow-Übersicht

```
1. File öffnen
   ↓
2. AI Suggestions Checkbox aktivieren ☑️
   ↓
3. Prompt eingeben (z.B. "Add docstring")
   ↓
4. LLM verarbeitet → Chat Tab zeigt Progress
   ↓
5. Background Tab zeigt: "Created X hunks: ..."
   ↓
6. Approval Modal erscheint (Modal-Fenster)
   ↓
7. ✓ Approve oder ✗ Reject pro Hunk
   ↓
8. "Apply Approved" Button
   ↓
9. Diff Viewer Modal zeigt Changes (grün/rot)
   ↓
10. ✓ Apply oder ✗ Cancel
   ↓
11. Chat Tab zeigt: "✓ Changes Applied"
    Background Tab zeigt: Details der Applied Hunks
```

## Beispiel: KI-Vorschläge Debugging

### Szenario: "returned no suggestions"

**Schritt 1:** Schaue ins **Chat Tab**
```
[AI] Checkbox checked
Sending to LLM...
returned no suggestions
```

**Schritt 2:** Gehe zu **AI Background Tab** (`Ctrl+A`)
```
[cyan]✓ Created 0 hunks:[/]
```

→ **Problem:** LLM gab leere Response. Warum?

**Schritt 3:** Scroll up im Background Tab um LLM Error zu sehen
```
ERROR: LLM call failed: All 1 providers exhausted: ['OpenAICompatibleClient']
```

→ **Lösung:** OpenAI API Key fehlt oder ungültig

---

## Taste & Keybindings für Tabs

| Taste | Aktion |
|-------|--------|
| `Ctrl+A` | Wechsel zu AI Background Tab |
| `Ctrl+Tab` | Nächster Tab (Editor-Area) |
| `Ctrl+Shift+Tab` | Vorheriger Tab (Editor-Area) |
| `q` / `Ctrl+Q` | App beenden |

---

## Was die Debug-Messages bedeuten

### AI Workflow Messages

```
[dim]Sending to LLM...[/]
→ Anfrage wird an OpenAI/Ollama gesendet
   Dauert typisch 2-5 Sekunden

[dim]Parsing response...[/]
→ LLM-Response wird analysiert
   Sucht nach Code-Blöcken

[cyan]✓ Created 2 hunks:[/]
  [0] test.py:1-10 (5 lines)
  [1] test.py:15-20 (3 lines)
→ Erfolgreich! 2 Code-Changes gefunden
   Hunk [0]: Zeilen 1-10, 5 Änderungen
   Hunk [1]: Zeilen 15-20, 3 Änderungen

Ready for approval: 2 changes
→ Modal wird angezeigt
```

### Approval-Messages

```
Hunks: 0/2 approved
→ Du hast noch keine Hunks bestätigt

Hunks: 2/2 approved
→ Alle Hunks sind bestätigt, "Apply Approved" Button wird aktiv

✓ Changes Applied
Approved: 2/2 hunks
File: test.py
→ Alles erfolgreich angewendet!
```

---

## Troubleshooting

### Problem: Modal erscheint nicht
1. Schaue ins **AI Background Tab** (`Ctrl+A`)
2. Suche nach `ERROR: ...`
3. Häufige Fehler:
   - `All 1 providers exhausted` → API Key Problem
   - `Connection refused` → Ollama läuft nicht

### Problem: "Approved: 0/2" aber ich hab Approve geklickt
1. **Background Tab** öffnen
2. Suche nach `Created X hunks`
3. Wenn nur Zeile mit original_line == modified_line: LLM hat keine echten Changes geliefert
4. Versuche klareren Prompt

### Problem: Diff Viewer zeigt nichts
1. Approve Modal zeigt "Details" Button
2. Klick Details um die Hunks nochmal zu sehen
3. Falls leer: LLM gab keine Changes zurück

---

## Best Practices

1. **Immer Background Tab offen halten** beim Debugging
   - `Ctrl+A` um schnell dahin zu springen
   - Scroll up für vollständigen Log

2. **Klare Prompts geben**
   - ✅ "Add docstring to the process_data function"
   - ❌ "Make this better"

3. **LLM Provider prüfen**
   - `kicli-assist doctor` zeigt configured LLM
   - OpenAI: API Key in `ki.yaml` nötig
   - Ollama: Muss laufen auf `http://localhost:11434`

4. **File vor Änderungen speichern**
   - AI arbeitet auf dem letzten saved State
   - Unsaved Changes können zu unerwarteten Ergebnissen führen
