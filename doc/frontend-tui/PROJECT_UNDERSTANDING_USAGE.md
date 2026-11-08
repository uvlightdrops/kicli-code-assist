---
title: Project Understanding in TUI
project: kicli-code-assist
scope: frontend-tui
purpose: |
  User-facing documentation for the Project Understanding feature in the TUI.
  Explains how to use Ctrl+U to analyze external projects and view results.
created: 2026-11-08 00
updated: 2026-11-08 00
update_reason: Initial implementation and user guide
status: active
semantic_blocks:
  - id: quick-start
    title: Quick Start
  - id: step-by-step
    title: Step-by-Step Workflow
  - id: ui-components
    title: UI Components
  - id: analysis-depths
    title: Analysis Depth Levels
  - id: reading-report
    title: Reading the Analysis Report
  - id: tips-and-tricks
    title: Tips & Tricks
relations:
  - target: ../../../doc/backend/layer-3-autonomous-agent/PROJECT_UNDERSTANDING_SYSTEM.md
    type: reference
    reason: Technical implementation details
  - target: ./KEYBINDINGS.md
    type: reference
    reason: Complete keybinding reference including Ctrl+U
---

## Quick Start [quick-start]

1. **Select a Project Folder** in the file browser (left panel)
2. **Press `Ctrl+U`** to start analysis
3. **Choose Depth** (default: "detailed") in the dialog
4. **Wait** for analysis to complete (2-10 seconds depending on project size)
5. **View Results** in the "📊 Project" tab (right panel)

---

## Step-by-Step Workflow [step-by-step]

### Step 1: Select Project Folder

Use the **file browser (left panel)** to navigate to your project:

```
📁 dev_flow
  📁 kicli-code-assist  ← Current folder
  📁 ypipe              ← Select this to analyze ypipe
  📁 ki-core
```

- Use **↑/↓** to navigate
- Press **Enter** to select folder
- Status bar shows current selection

### Step 2: Trigger Analysis (Ctrl+U)

Press **`Ctrl+U`** from anywhere in the TUI:

```
┌────────────────────────────────┐
│ 📊 Analyze Project: /path/ypipe│
├────────────────────────────────┤
│ Depth (default: detailed):     │
│ [detailed________________]     │
│                                │
│ [Analyze]  [Cancel]            │
└────────────────────────────────┘
```

### Step 3: Choose Analysis Depth

Enter analysis depth in the dialog:

- **`overview`** - Quick scan (30-60 seconds, brief report)
- **`detailed`** (default) - Full analysis (2-5 seconds, comprehensive)
- **`deep`** - Exhaustive analysis (placeholder for future LLM integration)

Press **`Enter`** to start or **`Esc`** to cancel.

### Step 4: Monitor Progress

Status bar shows analysis progress:

```
⏳ Analyzing project... (this may take a moment)
```

UI remains responsive during analysis (async background worker).

### Step 5: View Results

Auto-switches to the **"📊 Project"** tab when done:

```
┌──────────────────────────────────────────┐
│ 💬 Chat │ 💻 Debug │ 📊 Project │ ...    │ ← Click here or result auto-opens
├──────────────────────────────────────────┤
│                                          │
│ # ypipe - Comprehensive Understanding    │
│                                          │
│ ## Executive Summary                     │
│ The project comprises 18 modules with    │
│ 1160 lines of code. It follows 4         │
│ distinct architectural patterns...       │
│                                          │
│ ## Purpose & Core Architecture           │
│ **Architectural Patterns**:              │
│ - Factory Pattern                        │
│ - Pipeline/Processing Pattern            │
│ - Modular Architecture                   │
│ - Configuration-Driven                   │
│                                          │
│ ... (full report) ...                    │
│                                          │
│ 📈 Metrics:                              │
│   Modules: 18                            │
│   LOC: 1160                              │
│   Dependencies: 25                       │
│   Patterns: Factory Pattern, ...         │
└──────────────────────────────────────────┘
```

---

## UI Components [ui-components]

### ProjectUnderstandingPanel (📊 Project Tab)

**Purpose:** Displays comprehensive project analysis results

**Features:**

| Feature | Description |
|---------|-------------|
| **Title** | Shows project name and "Understanding Analysis" header |
| **Synthesis Report** | Main analysis content (2-5KB, truncated for display) |
| **Metrics Footer** | Shows key statistics (modules, LOC, dependencies) |
| **Loading State** | Spinner animation "⠋ Analyzing..." during processing |
| **Auto-Scrolling** | Focuses on report when analysis completes |

**Controls:**

- **Scroll:** Use `↑/↓` or `Page Up/Down` to navigate report
- **Search:** Use `Ctrl+F` to find text in report
- **Export:** Future feature (Ctrl+E) will save full report

### Analysis Dialog

**Purpose:** Prompt user for analysis depth selection

**Layout:**

```
┌─────────────────────────────────┐
│ 📊 Analyze Project: /path/name  │
├─────────────────────────────────┤
│ Depth (default: detailed):      │
│ [input field________________]   │
│                                 │
│  [Analyze]  [Cancel]            │
└─────────────────────────────────┘
```

**Interaction:**
- Type depth value: `overview`, `detailed`, or `deep`
- Press `Enter` to start analysis
- Press `Esc` to cancel
- Dialog closes automatically after starting

### Status Notifications

**During Analysis:**
```
⏳ Analyzing project... (this may take a moment)
```

**On Success:**
```
✅ Analysis complete: ypipe
```

**On Error:**
```
❌ Analysis failed: Project not found
```

Notifications auto-clear after 2-3 seconds.

---

## Analysis Depth Levels [analysis-depths]

### Overview (Fast)
- **Time:** 1-2 seconds
- **Scope:** High-level structure only
- **Content:** Project summary, main abstractions, patterns
- **Use Case:** Quick project overview, CI/CD pipelines
- **Future:** Will disable heavy analysis steps

### Detailed (Default, Recommended)
- **Time:** 2-5 seconds
- **Scope:** Full analysis across all 12 aspects
- **Content:** Complete synthesis report with metrics
- **Use Case:** Developer understanding, architecture review
- **Current Implementation:** Full pipeline (Discovery + Structure + Synthesis)

### Deep (Comprehensive, Future)
- **Time:** 10-30 seconds (with LLM)
- **Scope:** Including LLM-generated insights
- **Content:** Detailed analysis + AI recommendations
- **Use Case:** In-depth code review, hiring/onboarding
- **Future Enhancement:** Will call LLM API for advanced insights

---

## Reading the Analysis Report [reading-report]

### Report Structure

The synthesis report covers **12 analysis aspects** organized hierarchically:

#### 1. Executive Summary
High-level overview of project purpose and scope.

```
The project comprises 18 modules with 1160 lines of code. 
It follows 4 distinct architectural patterns and depends on 25 external packages.
```

#### 2. Purpose & Core Architecture
Project mission and main design approach.

```
**Architectural Patterns**:
- Factory Pattern
- Pipeline/Processing Pattern
- Modular Architecture
- Configuration-Driven
```

#### 3. Code Organization
Module breakdown and LOC distribution.

```
- Total Modules: 18
- Total LOC: 1160
- Average Module Size: 64 LOC
```

#### 4. Key Abstractions
Main classes and their roles.

```
- Task: Base class for all executable units
- Pipeline: Orchestrator combining tasks
- Context: Runtime execution context
```

#### 5. External Dependencies
Third-party packages used.

```
The project uses 25 external packages:
- yaml
- pandas
- pydantic
- networkx
- jinja2
- ... (and 20 more)
```

#### 6-12. Additional Sections
Module details, internal dependencies, goals, and next steps.

### Interpreting Metrics

**Total Modules:** Higher = more complex, but potentially better organized

**LOC per Module:** 50-100 is ideal; >300 suggests refactoring needed

**External Dependencies:** Fewer is better; >20 may indicate tight coupling

**Patterns Detected:**
- More patterns = more sophisticated architecture
- Common patterns (Factory, Pipeline) indicate good design practices

### Understanding Architectural Patterns

| Pattern | Indicates |
|---------|-----------|
| **Factory Pattern** | Flexible object creation, good abstraction |
| **Pipeline/Processing** | Staged execution, data transformation focus |
| **Modular Architecture** | Good separation of concerns |
| **Configuration-Driven** | Flexible, externally configurable behavior |
| **Service/API Pattern** | Clear service boundaries, API design |

---

## Tips & Tricks [tips-and-tricks]

### Tip 1: Analyze Before Deep Dive
Run analysis on any project before reading the code to understand its structure quickly.

### Tip 2: Use for Onboarding
New team members: Run analysis on project to understand architecture in 2 minutes.

### Tip 3: Compare Projects
Analyze multiple projects to understand their different architectural approaches.

### Tip 4: Save Analysis Results
Future feature (Ctrl+E) will export full report for sharing with team.

### Tip 5: Check External Dependencies
Look at dependency list to understand external constraints and design choices.

### Tip 6: Pattern Detection Hints
- **No patterns detected** = Simple, straightforward code (good or bad?)
- **Many patterns** = Complex architecture (necessary or over-engineered?)
- **Factory + Pipeline** = Typical data processing pipeline project

### Tip 7: Slow Projects
If analysis takes >10 seconds, project is large (1000+ modules) - consider breaking it down.

### Troubleshooting

**Q: Analysis shows "No file selected"**
- A: Click on a folder in the file browser (left panel) first, then press Ctrl+U

**Q: Analysis seems stuck**
- A: Check status bar - it should show "Analyzing...". Wait up to 10 seconds.
- A: If frozen >15 seconds, close and reopen TUI (rare edge case)

**Q: Results show errors**
- A: Check project_root validity - path must be readable directory
- A: Python files must be valid syntax (some analysis skips broken files)

**Q: Report is truncated**
- A: Full report is available in the panel - scroll down
- A: Future: Ctrl+E will export complete report to file

---

## Keyboard Reference

| Key | Action |
|-----|--------|
| **Ctrl+U** | Start project analysis (Understand Project) |
| **↑/↓** | Scroll report in Project tab |
| **Page Up/Down** | Page scroll report |
| **Ctrl+F** | Search text in report (Preview panel) |
| **Esc** | Close dialog (if open) |

See [KEYBINDINGS.md](./KEYBINDINGS.md) for complete reference.

---

## Example Workflow: Understanding ypipe

1. **Open TUI** in kicli-code-assist directory
2. **Navigate** file browser to `/home/flow/dev_flow/ypipe`
3. **Press `Ctrl+U`**
4. **Enter `detailed`** (or just press Enter for default)
5. **Wait** ~3-5 seconds
6. **Read report** in the "📊 Project" tab

**Report shows:**
- ✅ 18 modules, 1160 LOC
- ✅ 4 patterns: Factory, Pipeline, Modular, Config-Driven
- ✅ 12 key abstractions: Task, Pipeline, Context, etc.
- ✅ 25 dependencies: yaml, pandas, pydantic, etc.
- ✅ Goals from docs (if available)

---

## Future Enhancements

- **LLM Integration:** Generate AI insights with "deep" analysis level
- **Export:** Ctrl+E to save full report to file
- **Comparison:** Analyze two projects side-by-side
- **Visualization:** Generate architecture diagrams
- **Multi-Language:** Support JavaScript, Go, Rust, etc.
