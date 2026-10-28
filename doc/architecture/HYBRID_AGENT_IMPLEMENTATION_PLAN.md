# Hybrid Agent + Diff Viewer Implementation Plan

## User Requirements Analysis

Your use case: **Agentic Programming from Scratch**
- Single LLM chat interface that routes to multiple agents
- Project creation/navigation via agents (not UI buttons)
- Automatic structure + metrics analysis (not separate)
- Code review with inline diffs in tabs
- Scope control: folder-level vs. project-level analysis

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ UNIFIED AGENT CHAT (Top Panel)                              │
│ "Create a REST API endpoint for users"                      │
│ [Folder▼] [Project-wide▼] [Send]                            │
├─────────────────────────────────────────────────────────────┤
│ AGENT ROUTER (Backend Intelligence)                         │
│   • Parse intent → determine agent(s)                        │
│   • Route to: Structure + Metrics (always together)          │
│   • Route to: Dependencies, Refactor, etc. (if relevant)     │
├─────────────────────────────────────────────────────────────┤
│ RESULT PANELS (Auto-render based on content)                │
│ [Summary] [Structure] [Metrics] [Review] [Diff] [...]       │
│                                                              │
│ Diff Viewer with Tabs:                                       │
│ ├─ file1.py [Diff]                                          │
│ ├─ file2.py [Diff]                                          │
│ └─ file3.py [Diff]                                          │
│                                                              │
│ Inline diffs: ✓ Add (green), ✗ Remove (red), ~ Change (blue)│
├─────────────────────────────────────────────────────────────┤
│ SETTINGS (Right Sidebar)                                    │
│ Parsing Scope: ⦿ Folder Only  ○ Project-Wide               │
│ Auto-review:   ✓ Enable diffs on file changes               │
│ Tab Strategy:  ○ Tabs  ○ Sidebar  ○ Split View             │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Chat Input + Auto-Execution

### UnifiedAgentChat Component

```tsx
// Purpose: Single chat interface routing to multiple agents
// Location: components/UnifiedAgentChat.tsx

Features:
  ✓ Text input with multiline support
  ✓ Scope selector (Folder / Project-Wide)
  ✓ Settings access
  ✓ Loading spinner with token count
  ✓ Error boundary

State:
  - messages: ChatMessage[] (user + agent responses)
  - currentScope: 'folder' | 'project'
  - isLoading: boolean
  - agentSession: SessionContext

Flow:
  1. User types: "Explain this and show metrics"
  2. Send to /api/agent/route endpoint
  3. Router determines: [Explain, Metrics]
  4. Both run in parallel (async)
  5. Render results in tabs automatically
```

### Backend: Agent Router Endpoint

```python
# Purpose: Smart routing based on intent
# Endpoint: POST /api/agent/route
# This replaces multiple button clicks with one intelligent dispatch

Request:
{
  "query": "Explain this module and optimize it",
  "file_path": "src/pipeline.py",
  "scope": "folder" | "project",  # NEW: controls parsing depth
  "project": "ypipe"  # opened project
}

Response:
{
  "intent": "explain_with_optimization",
  "agents": [
    {
      "type": "explain",
      "result": {structure, imports, functions}
    },
    {
      "type": "metrics",
      "result": {maintainability_index, complexity}
    },
    {
      "type": "refactor",
      "result": {suggestions}
    }
  ],
  "session_id": "abc123"  # for follow-ups
}
```

---

## Phase 2: Diff Viewer with Tabs

### DiffViewer Component

```tsx
// Purpose: Display code changes with inline diffs
// Location: components/DiffViewer.tsx

Structure:
  ┌─ TabBar ────────────────────┐
  │  [file1.py] [file2.py] [+]  │ ← Add new file tab
  ├─────────────────────────────┤
  │ file1.py                    │
  │                             │
  │  5  │ def process():        │
  │ +6  │   new_line = True     │ ← Green (added)
  │  7  │   return data         │
  │ -8  │   old_code()          │ ← Red (removed)
  │  9  │                       │
  └─────────────────────────────┘

Features:
  ✓ Lazy-load files (only parse when tab opened)
  ✓ Inline diff highlighting
  ✓ Line numbers + change indicators
  ✓ File-level acceptance (✓ Accept All / ✗ Reject All)
  ✓ Line-level comments (for review)
  ✓ Syntax highlighting via Prism
```

### Tab Manager

```tsx
// Purpose: Auto-open tabs for edited files
// Hook: useDiffTabs()

Behavior:
  • Agent generates changes to 3 files
  • DiffTabs automatically creates tabs for each
  • First tab active, others lazy-loaded
  • User can accept/reject per-file or per-line
  • Clear history button

State Shape:
{
  tabs: [
    {
      id: "file1.py",
      filePath: "src/models/file1.py",
      status: "pending" | "accepted" | "rejected",
      diff: {original, modified},
      isLoaded: boolean
    }
  ],
  activeTabId: "file1.py"
}
```

---

## Phase 3: Settings Panel

### Parsing Scope Setting

```tsx
// Purpose: Control analysis depth
// Location: RightPanel > SettingsTab

Options:
  
  [×] Folder-Only Parsing
      └─ Analyzes only current file's folder
      └─ Fast, focused, good for feature development
      └─ Scope: src/models/* when file = src/models/user.py
      └─ Dependencies: only within folder

  [×] Project-Wide Parsing
      └─ Analyzes entire project (like PyCharm)
      └─ Slower, comprehensive, good for refactoring
      └─ Scope: src/**/* + tests/**/*
      └─ Dependencies: cross-project aware

Default: Folder-Only (faster feedback loops)

Implementation:
  • Pass scope to /api/agent/explain
  • DependencyAnalyzer respects scope
  • MetricsAnalyzer respects scope
  • UI shows [Project-Wide Analysis In Progress...]
```

---

## Phase 4: Integration Flow (Complete)

### User Journey: "Create a user authentication module"

**Step 1:** User types in chat
```
"Create a user authentication module with JWT, 
show me the structure and check for issues"
```

**Step 2:** Router analyzes intent
```
Detected agents: explain, metrics, refactor, suggest
Scope: project-wide (auto-detects "create from scratch")
Session: new_session_xyz
```

**Step 3:** Parallel execution
```
Agent 1: suggest   → "Create files: auth.py, models.py, routes.py"
Agent 2: explain   → "Current structure: X modules, Y functions"
Agent 3: metrics   → "Maintainability: 75/100"
Agent 4: refactor  → "Patterns to follow: dependency injection"
```

**Step 4:** Auto-render results
```
Tabs appear:
  [Summary]      ← Generated file structure + imports
  [Structure]    ← Explain output
  [Metrics]      ← Analysis
  [Recommendations] ← Refactor suggestions
  [Diffs]        ← Files to create/modify (tabs)
```

**Step 5:** User acts on diffs
```
Click: Accept all files
Action: Files written to disk
Follow-up: "Now implement the authentication logic"
```

---

## Technical Implementation Details

### Backend Changes

#### 1. `/api/agent/route` (NEW)
```python
@app.post("/api/agent/route")
async def route_agent_query(request: Request):
    data = await request.json()
    query = data.get("query")
    scope = data.get("scope", "folder")  # NEW
    project = data.get("project")
    file_path = data.get("file_path")
    
    # Intent detection via LLM
    intent = await detect_intent(query)  # GPT-4 "classify"
    
    # Route to multiple agents
    agents_to_run = []
    if intent.needs_structure:
        agents_to_run.append(("explain", file_path, scope))
    if intent.needs_metrics:
        agents_to_run.append(("metrics", file_path, scope))
    if intent.needs_refactor:
        agents_to_run.append(("refactor", file_path, scope))
    
    # Run in parallel
    results = await asyncio.gather(*[
        run_agent(agent, params) 
        for agent, *params in agents_to_run
    ])
    
    return {
        "intent": intent,
        "agents": results,
        "session_id": generate_session_id()
    }
```

#### 2. Scope Parameter in Analyzers
```python
# DependencyAnalyzer
def analyze_dependencies(
    root_path, 
    file_path, 
    scope="folder"  # NEW
):
    if scope == "folder":
        # Only scan folder containing file
        analysis_root = os.path.dirname(file_path)
    else:  # project
        # Scan entire project
        analysis_root = root_path
    
    # Rest of analysis
```

#### 3. Session Management
```python
# Store session context for follow-ups
sessions = {}  # session_id → AgentSession

class AgentSession:
    def __init__(self, session_id):
        self.id = session_id
        self.project_path = ""
        self.current_file = ""
        self.scope = "folder"
        self.files_changed = {}  # for diff tracking
        self.created_at = time.time()
```

### Frontend Changes

#### 1. New Hooks
```tsx
// hooks/useAgentRouter.ts
export function useAgentRouter() {
  const [session, setSession] = useState<AgentSession | null>(null);
  
  const routeQuery = async (query: string, scope: 'folder' | 'project') => {
    const response = await axios.post('/api/agent/route', {
      query,
      file_path: currentFile,
      scope,
      project: currentProject?.name
    });
    
    setSession(response.data);
    return response.data;
  };
  
  return { session, routeQuery };
}

// hooks/useDiffTabs.ts
export function useDiffTabs() {
  const [tabs, setTabs] = useState<DiffTab[]>([]);
  
  const addTabsFromDiffs = (diffs: FileDiff[]) => {
    const newTabs = diffs.map(diff => ({
      id: diff.filePath,
      filePath: diff.filePath,
      diff,
      status: 'pending',
      isLoaded: false
    }));
    setTabs(prev => [...prev, ...newTabs]);
  };
  
  return { tabs, addTabsFromDiffs };
}
```

#### 2. Component Tree
```
App
├─ ProjectManager
├─ FileExplorer
├─ UnifiedAgentChat (NEW)
│  ├─ ChatInput
│  ├─ ScopeSelector (NEW)
│  └─ MessageHistory
├─ RightPanel
│  ├─ TabBar (dynamic tabs)
│  ├─ SummaryPanel
│  ├─ StructurePanel (Explain)
│  ├─ MetricsPanel
│  ├─ DiffViewer (NEW)
│  │  ├─ TabManager
│  │  └─ InlineDiffDisplay
│  └─ SettingsPanel (NEW)
└─ StatusBar
   └─ TokenCounter
```

---

## Implementation Roadmap

### Week 1: Phase 1 - Chat Input + Router
- [ ] UnifiedAgentChat component
- [ ] /api/agent/route endpoint
- [ ] Intent detection (simple heuristics first, LLM later)
- [ ] Session context management
- **Deliverable:** Single chat input with auto-routing to Explain + Metrics

### Week 2: Phase 2 - Diff Viewer
- [ ] DiffViewer component with inline diffs
- [ ] TabManager with lazy-loading
- [ ] Accept/Reject logic
- [ ] File write handler
- **Deliverable:** Changes displayed in interactive tabs

### Week 3: Phase 3 - Settings + Polish
- [ ] Parsing scope selector
- [ ] Settings panel UI
- [ ] Scope logic in analyzers
- [ ] Follow-up messages (session context)
- **Deliverable:** Full control over analysis depth + conversational continuity

---

## Key Decisions Made

✅ **Chat-First but Analysis-Last**: Show results in your existing specialized panels  
✅ **Auto-Grouping**: Explain + Metrics always together (not separate clicks)  
✅ **Scope Flexibility**: Folder vs. Project control without UI clutter  
✅ **Diff-First Review**: Changes in interactive tabs, not batch apply  
✅ **Session Persistence**: Follow-ups understand prior context  
✅ **Lazy Loading**: Only parse files when tabs opened (performance)  

---

## Migration Path for Current Users

**Today:** Button-based analysis (works as before)  
**Tomorrow:** Chat-based + buttons coexist  
**Later:** Deprecate buttons, chat becomes primary  

No breaking changes needed; gradual transition.

---

## Success Criteria

- ✓ One chat input handles intent routing
- ✓ Structure + Metrics render together automatically
- ✓ User can control analysis scope (folder vs. project)
- ✓ Diffs show in tabs with inline highlighting
- ✓ Files accepted/rejected individually
- ✓ Follow-ups reference prior session context
- ✓ No manual "Select Agent" anymore
