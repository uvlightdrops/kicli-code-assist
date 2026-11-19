---
project: kicli-code-assist
scope: frontend-tui
title: Right Pane Architecture
created: 2026-11-19 22
updated: 2026-11-19 22
update_reason: Initial concept - 2-tab model reorganization (Chat vs Analysis)
status: planning
agent_project: kicli-code-assist
---

# Right Pane Architecture Concept

**Purpose**: Reorganize right pane tabs by function type (Chat-driven vs Standalone)

---

## 📊 Current Tabs Analysis

| Tab Name | Current Function | Type | LLM Dependent | UI Complexity | Status |
|----------|-----------------|------|--------------|---------------|--------|
| **Generate** | Code generation chat | Chat-driven | YES | Input + Display | ✅ Active |
| **Explain** | Code analysis | Standalone | YES | Response + Chunks | 🔄 Planned |
| **Metrics** | Code quality metrics | Standalone | YES | Response + Chunks | 🔄 Planned |
| **Refactor** | Refactoring suggestions | Standalone | YES | Response + Chunks | 🔄 Planned |
| **Suggest** | Improvement hints | Standalone | YES | Response + Chunks | 🔄 Planned |
| **Dependencies** | Dependency analysis | Standalone | YES | Response + Chunks | 🔄 Planned |
| **Reason** | Design rationale | Standalone | YES | Response + Chunks | 🔄 Planned |

---

## 🎯 Proposed Reorganization: 2-Tab Model

### **TAB 1: CHAT** (Primary - for iterative work)
**Function**: All chat-driven, multi-turn, conversational AI operations  
**Current Operations**:
- ✅ Code Generation (multi-file, iterative refinement)
- ✅ Multi-File Generation (save to project, auto-refresh)
- ⏳ Code Extension (modify existing files via chat)
- ⏳ Agent-based Coding (long-form reasoning + code)

**UI Elements**:
- Rich chat display (top, 70%)
- 3-line input box (bottom, 30%)
- History button (top-right)
- Send button (input-right)

**Characteristics**:
- Stateful conversation history
- Multi-turn interaction
- Real-time streaming responses
- File save integration
- Auto-refresh FileTree

---

### **TAB 2: ANALYSIS** (Secondary - for file inspection)
**Function**: One-shot, file-focused analysis of selected file  
**Operations**:
- 📊 Metrics: Code quality, complexity, maintainability
- 🔍 Explain: What does the file do? How is it structured?
- 🔧 Refactor: What improvements exist?
- 🏗️ Dependencies: Imports, circular deps, relationships
- 💡 Suggest: Best practices & improvements
- 🧠 Reason: Design decisions & rationale

**UI Elements**:
- File selector badge (top-left): "Analyzing: `config.py`"
- Split view (50/50):
  - **Top**: LLM Response (formatted)
  - **Bottom**: LLM Thinking/Chunks (stream)
- Analyze button (top-right, trigger re-analysis)
- Copy buttons (per section)

**Characteristics**:
- File-focused (selected file from FileTree)
- Single-shot analysis (Analyze button)
- Multiple analysis types (via sub-tabs or dropdown)
- Read-only results
- No state persistence

---

## 🔄 Interaction Model

```
User Workflow:

1. FILE INSPECTION FLOW (Analysis Tab):
   FileTree → Select File → Analysis Tab auto-updates
   → User clicks Analyze button → LLM runs → Display Explain/Metrics/Refactor options
   
2. CODE GENERATION FLOW (Chat Tab):
   → Switch to Chat Tab
   → Describe what to build: "Create a login form component"
   → Agent responds with code
   → User refines: "Make it responsive with dark mode"
   → Agent iterates
   → User clicks Save All → Files added to FileTree + Editor Tabs
   → Continue chatting for next feature
```

---

## 📐 Layout Changes Required

### Current Layout (Wrong):
```
┌─────────────────────────┐
│ [Analyze Button] 🔴     │  ← Wastes space, button not part of tab workflow
├─────────────────────────┤
│ Tab 1 | Tab 2 | Tab 3   │  ← Tabs scattered, no clear grouping
├─────────────────────────┤
│                         │
│ TAB CONTENT (mixed)     │
│                         │
└─────────────────────────┘
```

### Proposed Layout (Clean):
```
┌─────────────────────────┐
│ Chat | Analysis         │  ← Single top tab bar
├─────────────────────────┤
│                         │
│ TAB CONTENT:            │
│ - Chat: Display + Input │
│ - Analysis: Results     │
│                         │
└─────────────────────────┘
```

---

## 🛠️ Implementation Roadmap

### Phase A: Cleanup ✅ **COMPLETE**
- [x] Remove Analyze button from top
- [x] Move tab bar to top of pane
- [x] Increase chat input to 3 lines (now 4)
- [x] Reclaim vertical space
- [x] TUI tested without crashes

### Phase B: Tab Reorganization (NEXT)
- [ ] Split "Explain/Metrics/Refactor/etc" into Analysis tab
- [ ] Create Analysis sub-tab selector (dropdown or mini-tabs)
- [ ] Wire file selection → Analysis auto-trigger
- [ ] Update AgentTabContent for split-view layout

### Phase C: Chat Enhancement (LATER)
- [ ] Improve chat display formatting
- [ ] Add conversation threading
- [ ] Save chat history to project
- [ ] Code snippet highlighting in chat

### Phase D: Analysis Refinement (LATER)
- [ ] Real-time analysis as you type
- [ ] Comparison diffs (before/after refactor suggestions)
- [ ] Metrics dashboard view
- [ ] Dependency graph visualization

---

## 🎓 Key Decisions

1. **Why 2 tabs?**  
   Clear separation of concerns: interactive (Chat) vs inspective (Analysis)

2. **Why move Analyze button?**  
   It belongs in the Analysis tab workflow, not floating at top

3. **Why 3-line input?**  
   Better for multi-line prompts (current 1-line is too cramped)

4. **Future: Sub-tabs in Analysis?**  
   Each analysis type (Metrics/Explain/Refactor) could be its own tab,  
   or use dropdown selector to avoid tab clutter

---

## 📌 Orphaned Backend Endpoints (Phase B+)

Currently unused (see BACKEND_ANALYSIS.md):
- `/api/projects/analyze`
- `/api/projects/understand`

**Opportunity**: These could power the Analysis tab's multi-type selector:
- Route button clicks → correct backend endpoint
- Or consolidate into single `/api/files/analyze?type=explain|metrics|refactor`

**Decision Needed**: Backend team to decide on consolidation strategy.

---

## ✅ Success Criteria

### After Phase A ✅ **COMPLETE**
- [x] Single top tab bar visible
- [x] Analyze button gone
- [x] 4-line input box in Chat tab
- [x] No vertical space wasted
- [x] TUI loads without crashes
- [x] All functionality intact

### After Phase B (NEXT)
- [ ] Analysis tab consolidated
- [ ] File selection triggers Analysis
- [ ] Clear visual distinction (Chat vs Analysis)
- [ ] 50/50 split in Analysis tab (Response/Chunks)

---

## 📚 Related Documents

- **BACKEND_ANALYSIS.md** - Orphaned endpoint audit
- **Phase I2.3 UI Polish** - Previous tab work
- **TUI Layout Schema** - 3-pane layout reference

