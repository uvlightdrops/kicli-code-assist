---
title: TUI Attempt Oct 2026 - Archive & Learnings
scope: reference
project: kicli-code-assist
status: archived
created: 2026-11-05T22:02+01:00
updated: 2026-11-05T22:02+01:00
update_reason: Archive old chat-based TUI design; extract learnings for TUI 2.0
agent_project: kicli-code-assist
cross_references:
  - doc/specifications/02_PHASE_1_CHECKLIST.md (current implementation plan)
  - doc/archive/README.md (archive policy)
---

# TUI Attempt Oct 2026 — Archive & Learnings

## What Was This?

First attempt at building a TUI for kicli-code-assist (October 2026).

**Design:** File browser (left) + Chat (right) + Input (bottom)  
**Goal:** Interactive terminal interface for code analysis  
**Result:** Partially working; abandoned for agent-backend approach (Nov 2026)

## Why Archived?

1. **Architectural Pivot**: Project pivoted from simple chat to agent-backend orchestration
2. **Backend Evolution**: Phase 5.5.2 brought reasoning traces, multi-agent routing, transparency
3. **Better Approach**: Agent-backend approach leverages new capabilities; chat-only was limiting
4. **Complexity**: Chat-based design was growing complex without clear path to sophistication

## What We Learned

### ✅ What Worked Well

**Textual Framework:**
- Widget system solid for TUI
- Reactive state management intuitive
- Rich text markup powerful
- Keyboard binding flexible

**File Tree Navigation:**
- Vi-style navigation (Up/Down/Enter) intuitive
- File/folder icons helpful
- Current path tracking clear
- Directory traversal straightforward

**Async Operations:**
- `run_worker(thread=True)` pattern reliable
- UI stays responsive during LLM processing
- Spinner feedback helpful
- Threading approach simpler than `call_later(async)`

**Output Display:**
- RichLog excellent for streaming
- Auto-scroll works well
- Rich markup for formatting
- Multiple messages easy to handle

---

### ❌ What Didn't Work

**Chat-Based Interface:**
- Too conversational for code analysis
- Difficult to organize multi-mode responses (Explain, Suggest, Metrics, etc.)
- Context injection awkward with chat paradigm
- History explosion with code snippets

**Premature Complexity:**
- Tried to do file preview in Phase 1 (not needed)
- File context injection complicated message flow
- Session persistence attempted too early
- Performance optimization too early

**Design Decisions:**
- Single-mode chat unclear (what is this analyze doing?)
- No structure for agent routing
- No transparency into reasoning
- No way to visualize metrics/dependencies

---

### 🎯 Key Insights for TUI 2.0

**1. Embrace the Backend**
- Don't try to do analysis in TUI; use backend agents
- Let backend orchestrate; TUI just displays
- Leverage Phase 5.5.2 features (reasoning, transparency)

**2. Structured Output**
- Tabs per agent mode (not linear chat)
- Each tab has clear purpose (Explain, Metrics, Suggest, etc.)
- User chooses what to focus on

**3. Clear Focus**
- Phase 1: Scaffold only (tree + tabs + input + status)
- Phase 2: Streaming (all agents flowing)
- Phase 3: Intelligence (WebSocket, keyboard macros)
- Don't mix phases

**4. API-First Design**
- Separate Frontend Spec from implementation
- Define interface contract first
- TUI, WebUI, GTK can all implement same spec

**5. Async Patterns**
- `run_worker(thread=True)` works; stick with it
- Avoid `call_later(async def)` (blocks UI)
- Spinner + status bar good feedback

---

## What to Preserve (Borrowed for TUI 2.0)

### Keyboard Shortcuts (Pattern)
```
Browser Mode:
  UP/DOWN - Navigate
  ENTER - Select/Open
  TAB - Switch focus
  Q - Quit

Input Mode:
  ENTER - Submit
  TAB - Switch focus
  Up/Down - History
  Q - Quit
```

**Reused in Phase 1:**
- Tab switching (Ctrl+1-6 for agent tabs)
- Input history (Up/Down arrows)
- Focus management (Tab/Shift+Tab)
- Quit shortcut (Q)

### UI Layout Principles
```
┌─────────────────────────────────────┐
│  File Tree │ Agent Output Tabs      │
│           │                         │
├─────────────────────────────────────┤
│ Input Field                         │
├─────────────────────────────────────┤
│ Status Bar                          │
└─────────────────────────────────────┘
```

**Reused in Phase 1:** Same layout structure (fixed widths)

### Widget Structure
- `SelectableFileList` → `ProjectExplorer` (similar concept)
- `RichLog` for output → `AgentOutputPanel` (keep RichLog)
- `FocusAwareInput` → `InputField` (similar pattern)
- Custom widgets good approach

---

## Archived Files

### 02_TUI_SPECIFICATION_LEGACY.md
**Old Design Spec** — Chat-based interface requirements  
**Read when:** Understanding what Oct 2026 was trying to achieve

### 03_BACKEND_SPECIFICATION.md
**Old Backend Routes** — Chat session, project context, message format  
**Read when:** Understanding old message flow (don't use; use new routes)

### 04_FEATURE_CHECKLIST.md
**Old Feature Checklist** — Chat features (all "DONE" but now archived)  
**Read when:** Understanding old phase completeness (don't refer to for Phase 1)

### 05_IMPLEMENTATION_DETAILS.md
**Old Code Walkthrough** — FileList, ChatSession, ProjectContext classes  
**Read when:** Archaeology (don't use; rewrite for new design)

---

## When to Refer to This Archive

**Do refer to this when:**
- Learning why we pivoted from chat to agents
- Understanding Textual widget patterns
- Reviewing keyboard shortcut philosophy
- Understanding layout principles
- Looking at lessons learned

**Don't refer to when:**
- Building Phase 1 TUI scaffold
- Implementing widgets (rewrite; don't copy old code)
- Designing backend (new routes in FRONTEND_SPECIFICATION)
- Planning agent modes (new breakdown in TUI_INTELLIGENT_TERMINAL_IDE)

---

## What Happened Next?

**Nov 2026 Pivot:**
1. ✅ Created FRONTEND_SPECIFICATION (abstract, multi-frontend)
2. ✅ Created TUI_INTELLIGENT_TERMINAL_IDE (vision + phases)
3. ✅ Created Phase 1 Checklist (structured implementation)
4. ➡️ Starting Phase 1 implementation (week of Nov 5-8)

**Key Difference:**
- Oct 2026: "Build a chat TUI" (open-ended, too flexible)
- Nov 2026: "Build agent-backend TUI with clear phases" (structured)

---

## Links

**Active Documentation:**
- `doc/specifications/02_PHASE_1_CHECKLIST.md` — Current implementation plan
- `doc/architecture/FRONTEND_SPECIFICATION.md` — What to build
- `doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md` — Vision & phases
- `doc/archive/README.md` — Archive policy

**Legacy (this folder):**
- `02_TUI_SPECIFICATION_LEGACY.md` — Old design
- `03_BACKEND_SPECIFICATION.md` — Old routes
- `04_FEATURE_CHECKLIST.md` — Old features
- `05_IMPLEMENTATION_DETAILS.md` — Old code

---

**Archive Date:** 2026-11-05  
**Reason:** Superseded by agent-backend design (Nov 2026 pivot)  
**Preserve For:** Historical reference and lessons learned
