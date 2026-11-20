# 🎨 TUI Frame Minimalism - Visual Guide für Testsitzung

## Wie du die Unterschiede selbst siehst

### SCHRITT 1: Branch wechseln & TUI starten

```bash
# Terminal 1: Wechsel zur Experiment-Branch
cd /home/flow/dev_flow/kicli-code-assist
git checkout feature/tui-frame-minimalism
source .venv/bin/activate
kicli-assist tui

# → TUI startet mit MINIMALEN Rahmen (neue Version)
```

### SCHRITT 2: Worauf du achten solltest

#### 🔍 **Visuelle Merkmale - MINIMALE Version (Branch)**

| Element | Aussehen | Lage |
|---------|----------|------|
| **FileTree (links)** | Ohne dünnen Rahmen, nur Whitespace | Oben-links |
| **Tabbed Editor (links unten)** | Tab-Bar sichtbar, aber KEINE Box um Inhalt | Unten-links |
| **AgentTabs (rechts)** | Tabs oben, aber KEINE durchgehende Box um alles | Oben-rechts |
| **Chat Output (rechts)** | Nur Whitespace um Nachrichten, kein Rahmen | Mitte-rechts |
| **Input Field (unten)** | EINE Linie unter dem Input (nicht drum herum) | Unten |

**Gefühl:** Spacious, clean, minimal Chrome (Rahmen)

---

#### 🔍 **Visuelle Merkmale - VORHER (devel Branch)**

Wenn du später zur `devel` Branch wechselst, siehst du:

```bash
# Terminal: Branch wechsel
git checkout devel
kicli-assist tui
```

| Element | Aussehen | Unterschied |
|---------|----------|------------|
| **FileTree** | Mit DICKER RAHMEN (heavy border) | ← Viel sichtbarer |
| **Tabbed Editor** | Mit SOLIDEM Rahmen darum | ← Zusätzliche Box |
| **AgentTabs** | Mit SOLIDEM Rahmen darum | ← Doppelte Rahmung |
| **Chat Output** | Mit eigener innerer Box | ← 4-5 Rahmen tief! |
| **Input Field** | Mit SOLIDEM Rahmen darum | ← Box statt Line |

**Gefühl:** Heavy, viel Rahmen, "1990er ncurses" Ästhetik

---

## 🎬 Live-Vergleich durchführen

### Option A: Zwei Terminals nebeneinander

**Terminal 1 (neue Version):**
```bash
cd /home/flow/dev_flow/kicli-code-assist
git checkout feature/tui-frame-minimalism
kicli-assist tui
```

**Terminal 2 (alte Version):**
```bash
cd /home/flow/dev_flow/kicli-code-assist
git checkout devel
kicli-assist tui
```

→ Vergleiche nebeneinander und beobachte die Unterschiede! 

---

### Option B: Nacheinander vergleichen

```bash
# Step 1: Neue Version ansehen
git checkout feature/tui-frame-minimalism
kicli-assist tui
# → Schau die Layout an, beachte: wenig Rahmen, viel Whitespace
# → Drücke Ctrl+C zum Beenden

# Step 2: Alte Version ansehen  
git checkout devel
kicli-assist tui
# → Schau die Layout an, beachte: viele Rahmen, dicht
# → Drücke Ctrl+C zum Beenden

# Step 3: Back to Experiment
git checkout feature/tui-frame-minimalism
```

---

## 🎯 Konkrete Fragen während des Tests

Während du die TUI testest, frag dich:

### Visual Impact (Optik)
1. ✅ Fühlt sich die neue Version cleaner/spacious an?
2. ✅ Oder fühlt sie sich "leer" / "unfinished" an?
3. ✅ Ist der Unterschied zu den alten Rahmen deutlich?

### Usability (Benutzbarkeit)
4. ✅ Ist noch klar, welche Panel zu welcher Funktion gehört?
5. ✅ Kann man die Tabs noch gut erkennen (auch ohne Box um sie)?
6. ✅ Ist die Input-Linie unten gut erkennbar?

### Professional Feel
7. ✅ Wirkt die neue Version professioneller oder billiger?
8. ✅ Vergleich zu anderen CLIs (VS Code, lazygit, bottom)?
9. ✅ Würde ich die neue Version bevorzugen?

---

## 💡 Tipps für das Testen

### Was ist noch zu sehen:
```
┌─────────────────────────────────────────────────┐
│ Header (blau)                                   │
├─────────────────────────────────────────────────┤
│                                                 │
│ FileTree        │      Agent Tabs               │
│ 📄 file1.py     │  [Explain|Metrics|Refactor]  │
│ 📁 src/         │  ┌──────────────────────────┐ │
│                 │  │ Agent Response           │ │
│ [Tab1] [Tab2]   │  │ (Analyze, Refactor, etc) │ │
│ ┌──────────────┐ │  │                          │ │
│ │ File Content │ │  └──────────────────────────┘ │
│ │ ...code...   │ │  ┌──────────────────────────┐ │
│ └──────────────┘ │  │ Chat Output              │ │
│                 │  │ (Message history)        │ │
│ Chat Panel:     │  │                          │ │
│ ┌──────────────┐ │  └──────────────────────────┘ │
│ │ Messages     │ │                              │
│ │ ...text...   │ │  Input:                      │
│ └──────────────┘ │  [Type here...] [Send]      │
│                 │                              │
└─────────────────────────────────────────────────┘

NEUE VERSION (Experiment-Branch):
  - Keine dicker heavy-Border um linkes Panel
  - Keine solid Rahmen um einzelne Widgets
  - Nur single Linie unten beim Input
  - Viel Whitespace
  
ALTE VERSION (devel Branch):
  - Dicker Rahmen um alles (heavy border)
  - Solid Rahmen um Tabbed Editor
  - Solid Rahmen um Agent Tabs
  - Raum zwischen Rahmen gequetscht
```

---

## 🚀 Nach dem Test: Deine Entscheidung

Nach dem Ansehen, entscheide dich:

### Option 1️⃣ : "Neue Version ist besser!"
```bash
# Branch ist bereits experimental
# → Wir mergen sie in main (Production)
git checkout main
git merge feature/tui-frame-minimalism
git push
```

### Option 2️⃣ : "Zu leer / fehlt was"
```bash
# Wir verfeinern die CSS (z.B. subtile Borders zurück)
# Entweder hier im Branch editieren oder Ideen sammeln
```

### Option 3️⃣ : "Hybrid wäre besser"
```bash
# Z.B.: Tabbed Editor behält feinen Rahmen, Rest whitespace
# → Wir editieren die CSS entsprechend
```

---

## 📝 Checkliste für dich

Während du testest:

- [ ] TUI startet ohne Fehler
- [ ] FileTree sichtbar und nutzbar
- [ ] Tabs funktionieren (klickbar, Tab-Navigation)
- [ ] Content-Bereiche sichtbar und lesbar
- [ ] Input-Feld am unten erreichbar
- [ ] Kein Overflow/Clipping (alles passt)
- [ ] Fokus-Indikation noch klar (aktive Tab hervorgehoben?)
- [ ] Visuell angenehm oder zu sparse?

---

## ❓ Fragen nach dem Test (für mich)

Nach dem Ansehen der TUI, schreib mir:

1. **Visuelle Eindruck:**
   - "Die neue Version sieht ... aus" (clean/spacious/leer/professionell?)

2. **Vergleich:**
   - "Vs. alte Version: ... ist besser" (neue/alte/hybrid?)

3. **Konkrete Feedback:**
   - "Der [Panel/Element] fühlt sich an wie ..."
   - "Ich würde gerne ... ändern"

4. **Decision:**
   - "Merge jetzt?" / "Verfeinern zuerst?" / "Zurück zu alt?"

---

**Los geht's! 🎬**

```bash
# TUI starten (neue minimale Version):
cd /home/flow/dev_flow/kicli-code-assist
git branch  # check: sollte * feature/tui-frame-minimalism zeigen
source .venv/bin/activate
kicli-assist tui
```

Viel Spaß beim Testen! 🎉
