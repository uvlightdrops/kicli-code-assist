# Programming Agent UI Architecture: Current Approaches & Recommendations

**Date:** October 27, 2026  
**Author:** kicli-code-assist Team  
**Document:** Strategic Analysis of Agent UI/UX Patterns for Code Analysis IDEs

---

## Executive Summary

This document analyzes contemporary UI patterns for programming agents across major platforms (GitHub Copilot, VS Code, JetBrains IDEs) and provides evidence-based recommendations for kicli-code-assist's agent interface architecture.

### Key Findings
- **Unified input model preferred**: Chat interface as primary entry point with agent type selection
- **Contextual task delegation**: Different tasks (analysis, generation, reasoning) use same input but different execution paths
- **Workspace integration critical**: Agents need direct access to editor, files, terminal within unified workspace
- **Progressive disclosure**: Show capabilities progressively based on task complexity

---

## Current Industry Patterns

### 1. GitHub Copilot / VS Code (2024-2025 Model)

**Architecture:**
```
Chat Input Box (Primary Interface)
    ↓
Slash Commands (/explain, /fix, /test)
    ↓
Agent Selection (via @mentions or session config)
    ↓
Execution with inline tools
    ↓
Integrated diff/review in workspace
```

**Characteristics:**
- **Single input point**: Unified chat input for all interactions
- **Flexible routing**: Same input box routes to different analyzers/agents
- **Session-based**: Maintains context across multiple turns
- **In-situ changes**: Results displayed in editor, not separate windows
- **Tool integration**: Direct terminal, debugger, test runner access

**UI Components:**
- Chat View (left sidebar or tab)
- Agents Window (dedicated workspace coordination)
- Inline Chat (in-editor modifications)
- Quick Chat (lightweight temporary conversations)

**Evidence:**
- VS Code official documentation emphasizes "work with an agent in the same workspace as your editor, terminal, tests, and debugger"
- Users can inspect changes and investigate failures without leaving the IDE
- Parallel sessions with context switching

### 2. JetBrains IDEs (AI Assistant 2024-2025)

**Architecture:**
```
Chat Interface
    ↓
Agent Selection Panel (Junie, Claude, Codex, Copilot)
    ↓
External Agents via Agent Client Protocol (ACP)
    ↓
Context Management (#file, #codebase, #symbol)
    ↓
Integrated Changes Review
```

**Characteristics:**
- **Modular agents**: Multiple agent implementations behind unified chat
- **Protocol-based**: Agent Client Protocol allows external agents
- **Explicit context**: Users tag context with `#` mentions
- **Flexible backends**: Supports local models, bring-your-own-key, subscriptions
- **In-IDE workflow**: All operations within IDE context

**UI Components:**
- AI Chat sidebar
- Agent selection dropdown
- Context mention system
- Code review/diff in inspector

### 3. Comparing Analysis-First vs. Chat-First Approaches

#### Analysis-First (Your Current Model)
```
File Browser → Select Agent Type (Explain, Reason, Analyze)
                    ↓
            Execute Specific Analysis
                    ↓
            Display Specialized Panel
```

**Pros:**
- Clear visual affordance for each function
- Dedicated UI per analysis type
- Non-specialist users understand flow clearly
- Specialized layouts per analysis type

**Cons:**
- UI complexity (5+ separate panels/buttons)
- Context switching overhead
- Harder to combine analyses in workflows
- Each agent re-learns context independently
- Duplicated input validation

#### Chat-First (Copilot/VS Code Model)
```
Unified Chat Input
        ↓
Natural language + Agent selector
        ↓
Smart routing (explain vs. reason vs. refactor)
        ↓
Contextual output (panel, inline, chat, modal)
```

**Pros:**
- Single, consistent interaction model
- Natural language discovery (users ask "what do you think about this code?")
- Context reuse across multiple analyses
- Conversational refinement (follow-up questions)
- Reduced cognitive load
- Easier to add new analyses

**Cons:**
- Requires more LLM understanding of user intent
- Less explicit about what each agent does
- May intimidate non-technical users
- Requires better error messaging

---

## Current State: kicli-code-assist

### Layout Analysis

**Right Panel Current Structure:**
```
┌─────────────────────────────────────────┐
│  Right Sidebar                          │
├─────────────────────────────────────────┤
│  [Chat] [Agent] ← Tab selector          │
├─────────────────────────────────────────┤
│                                         │
│  Chat Tab:                              │
│  - Message input                        │
│  - Conversation history                 │
│                                         │
│  Agent Tab:                             │
│  - Explain button                       │
│  - Suggest button                       │
│  (Other agents not visible in this view)│
├─────────────────────────────────────────┤
│  Bottom: Agent type selector?           │
│  (mentioned but not shown in current)   │
└─────────────────────────────────────────┘
```

### Component Overview

**Current Components:**
1. **AgentPanel.tsx** - Explain, Suggest
2. **DependencyPanel.tsx** - Dependency analysis
3. **ReasoningPanel.tsx** - Multi-step reasoning
4. **MetricsPanel.tsx** - Code metrics
5. **RefactoringPanel.tsx** - Refactoring suggestions
6. **EnsemblePanel.tsx** - LLM voting

**Architecture Issue:** Each panel is independent; no unified input model.

---

## Research-Backed Recommendations

### Recommendation 1: Adopt Unified Input Model (High Priority)

**Based on:** VS Code, JetBrains, recent AI IDE research

**Implementation:**
```
┌────────────────────────────────────────────────────┐
│ Programming Agent Interface (Unified)              │
├────────────────────────────────────────────────────┤
│                                                    │
│  Input Section:                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ What would you like me to analyze?           │ │
│  │ [Text input field - full width]              │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Context Toolbar:                                  │
│  [File: pipeline.py] [Selection: lines 20-40]    │
│  [#codebase] [#tests] [Clear Context]            │
│                                                    │
│  Agent Type Selector:                              │
│  ⬤ Auto-detect  ○ Explain  ○ Analyze             │
│  ○ Refactor     ○ Reason   ○ Ensemble            │
│                                                    │
│  [Analyze] [↻ Show Details]                       │
│                                                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  Results Section:                                  │
│  ┌──────────────────────────────────────────────┐ │
│  │ Execution Time: 1.2s  Status: ✅ Complete   │ │
│  │                                              │ │
│  │ Multi-pane Output:                           │ │
│  │ [Summary] [Details] [Dependencies] [Metrics] │ │
│  │                                              │ │
│  │ [Summary Tab Active]                         │ │
│  │ ─────────────────────────────────────────   │ │
│  │ • 3 classes, 20 functions                   │ │
│  │ • Maintainability: 72/100 (Good)            │ │
│  │ • 5 high-priority refactoring suggestions   │ │
│  │                                              │ │
│  │ [Expand Details]                             │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Benefits:**
- Single, discoverable interface
- Users ask questions naturally: "What can I improve about this code?"
- Intelligent routing: same question → multiple analyses
- Conversational refinement: "Tell me more about the dependencies"

**Implementation Phases:**
1. Phase 1: Add unified chat input to right panel
2. Phase 2: Migrate Explain/Suggest to use chat input
3. Phase 3: Auto-route based on agent type selector
4. Phase 4: Context window persistence across analyses
5. Phase 5: Conversational follow-ups

---

### Recommendation 2: Specialized Panels via Tab System (Medium Priority)

**Current State:** Panels are separate components

**Proposed:** Keep panels but unified input feeds all of them

```
Agent Input
    ├─→ [Auto-detect] → Runs all relevant analyses
    ├─→ [Explain] → Shows ExplainPanel only
    ├─→ [Reason] → Shows ReasoningPanel only
    ├─→ [Dependencies] → Shows DependencyPanel only
    └─→ [Metrics] → Shows MetricsPanel only
```

**UI Layout:**
```
┌────────────────────────────────────────────────────┐
│ Input Section (Unified Chat)                       │
│ [What would you like to analyze?] [Agent▼]        │
│ [Analysis] [Clear]                                │
├────────────────────────────────────────────────────┤
│ [Summary] [Code] [Dependencies] [Refactor] [Tests]│
│                                                    │
│ Active Panel: Results displayed here              │
│ (Different content based on agent type)           │
└────────────────────────────────────────────────────┘
```

---

### Recommendation 3: Context Management (High Priority)

**Problem:** Each analysis learns context independently

**Solution:** Implement context window per session

```
Session Architecture:
┌─────────────────────────────────┐
│ Agent Session                   │
│  - Selected file                │
│  - Code selection (if any)      │
│  - Previous analyses results    │
│  - Settings (model, temperature)│
│  - Conversation history         │
└─────────────────────────────────┘
        ↓
┌─────────────────────────────────┐
│ All agent endpoints receive:    │
│  - file path                    │
│  - project path                 │
│  - session context              │
│  - conversation history         │
└─────────────────────────────────┘
```

**Implementation:**
- Store session state in React Context
- Persist to localStorage
- Share across all panel components
- Enable: "Why did you suggest this?" → Explain shows reasoning

---

### Recommendation 4: Progressive Disclosure (Medium Priority)

**Current Issue:** 6 agent buttons overwhelming for beginners

**Solution:** Show capabilities based on complexity

**Level 1 (Beginners):** Basic analysis
```
[Analyze Code] 
```

**Level 2 (Experienced):** Multiple analysis types
```
[Explain] [Suggest] [Analyze Details]
```

**Level 3 (Advanced):** Full agent control
```
Agent Type: [Auto-detect▼]
[Explain] [Reason] [Refactor] [Metrics]
[Dependencies] [Ensemble] [Stream]
```

---

## Synthesis: Recommended Architecture for kicli-code-assist

### Phase 1: Short-term (Next Sprint)
✅ **Keep current structure but improve**
- Unify all panel API calls (project parameter) ← **DONE**
- Add context management layer
- Implement session persistence

### Phase 2: Medium-term (2-3 Sprints)
🔄 **Introduce unified chat input**
- Keep specialized panels
- Add "Unified Agent Input" above current tabs
- Route input to all relevant analyses simultaneously
- Show results in tabs

```
┌─────────────────────────────────────────┐
│ UNIFIED INPUT LAYER                     │
│ [Ask me anything about this code] [▼]   │
│ [File: pipeline.py] [Line: 50-100]      │
│ [Run All Analysis] [Clear]              │
├─────────────────────────────────────────┤
│ [Chat] [Explain] [Reason] [Metrics]     │ ← Tabs with results
│         [Dependencies] [Refactor] [...]  │
├─────────────────────────────────────────┤
│                                         │
│ (Active panel content here)             │
│                                         │
└─────────────────────────────────────────┘
```

### Phase 3: Long-term (4+ Sprints)
🎯 **Full unified agent model**
- Single input interface (like Copilot)
- Multi-tab output (all results available)
- Conversational mode (follow-up questions)
- Smart agent selection (understand user intent)
- Cross-analysis context preservation

---

## Comparative Analysis: Your Model vs. Industry Standard

| Aspect | Your Current | Chat-First | Hybrid (Recommended) |
|--------|-------------|-----------|---------------------|
| **Discovery** | Panel buttons | Natural language | Both |
| **Interaction** | Multi-step | Conversational | Conversational with tabs |
| **Context reuse** | Per-panel | Cross-session | Cross-session |
| **Complexity** | Moderate | Low UI, High LLM | Low UI+UX |
| **Beginner UX** | Clear but many buttons | Intuitive | Intuitive with guides |
| **Power user UX** | Limited workflows | Flexible chaining | Flexible + specialized panels |
| **Implementation** | Current baseline | High refactor | Incremental |

---

## Implementation Strategy

### Why Hybrid (Not Fully Replaced)

1. **Your specialized panels are valuable**
   - DependencyPanel with graph visualization (not easy in chat)
   - MetricsPanel with rich statistics UI
   - ReasoningPanel with step-by-step thinking display

2. **Unified input adds affordance**
   - Users don't need to know about 6 different buttons
   - Conversational flow more natural
   - Context automatically managed

3. **Incremental migration possible**
   - Phase 1: Add input layer, keep panels separate
   - Phase 2: Cross-panel context
   - Phase 3: Smart routing
   - No breaking changes

---

## Technical Implementation Roadmap

### Phase 1: Context Window (Week 1-2)
```typescript
// Session-scoped context
interface AgentSessionContext {
  selectedFile: string | null;
  selectedCode?: string;
  projectPath: string;
  analyses: {
    explain?: ExplainResult;
    reason?: ReasoningResult;
    metrics?: MetricsResult;
    dependencies?: DependencyResult;
    refactor?: RefactorResult;
  };
  conversationHistory: Array<{
    role: 'user' | 'agent';
    content: string;
    timestamp: number;
  }>;
}

// Create AgentSessionProvider
export const AgentSessionProvider: React.FC = ({ children }) => {
  const [session, setSession] = useState<AgentSessionContext>(loadSession());
  useEffect(() => saveSession(session), [session]);
  return <AgentSessionContext.Provider value={{ session, setSession }} />;
};
```

### Phase 2: Unified Input (Week 2-3)
```typescript
// UnifiedAgentInput.tsx
export const UnifiedAgentInput: React.FC = () => {
  const { session, setSession } = useAgentSession();
  const { current: currentProject } = useProject();
  
  const handleAnalyze = async (query: string, agentType: 'auto' | 'explain' | 'reason' | 'all') => {
    // Route to appropriate endpoints
    const analyses = await Promise.all([
      agentType === 'auto' || agentType === 'all' 
        ? explainCode(session.selectedFile, currentProject)
        : null,
      agentType === 'auto' || agentType === 'reason' || agentType === 'all'
        ? reasonAboutCode(session.selectedFile, query, currentProject)
        : null,
      agentType === 'auto' || agentType === 'all'
        ? analyzeMetrics(session.selectedFile, currentProject)
        : null,
    ]);
    
    setSession(prev => ({
      ...prev,
      analyses: {
        ...prev.analyses,
        explain: analyses[0],
        reason: analyses[1],
        metrics: analyses[2],
      }
    }));
  };
};
```

### Phase 3: Tab-based Result Display (Week 3-4)
```typescript
// ResultsTabs.tsx
export const ResultsTabs: React.FC = () => {
  const { session } = useAgentSession();
  const availableTabs = Object.entries(session.analyses)
    .filter(([_, result]) => result !== null)
    .map(([key]) => key);
  
  return (
    <TabBar>
      {availableTabs.map(tab => (
        <Tab key={tab} label={tabLabel(tab)} active={activeTab === tab}>
          {renderPanel(tab, session.analyses[tab])}
        </Tab>
      ))}
    </TabBar>
  );
};
```

---

## Metrics for Success

### UX Metrics
- **Discoverability**: Can new users find all agent types? Target: 90%+ in onboarding tests
- **Interaction time**: Average time from file selection to first result. Target: <3 seconds
- **Feature usage**: Distribution of agent type usage. Target: Even distribution (no single type >40%)

### Performance Metrics
- **Parallel analysis speedup**: Time(all analyses) vs sum(individual). Target: 80%+ parallelization
- **Context reuse**: Follow-up analysis using cached context. Target: 50% faster

### Adoption Metrics
- **Agent panel usage**: % of coding sessions using agent. Target: >60%
- **Multi-agent workflows**: % of sessions using >1 agent type. Target: >30%

---

## Research Sources & References

1. **VS Code Agent Architecture (2024-2025)**
   - Source: https://code.visualstudio.com/docs/agents/overview
   - Pattern: Unified chat interface with specialized tools
   - Key insight: "Work with an agent in same workspace as editor, terminal, tests"

2. **GitHub Copilot UI/UX Evolution**
   - Pattern: Single input point, flexible output routing
   - Shift from command-based to conversational

3. **JetBrains AI Assistant**
   - Pattern: Agent selection + chat interface
   - Innovation: Agent Client Protocol (ACP) for extensibility

4. **Human-AI Interaction Research**
   - Finding: Users prefer conversational over command-based interfaces
   - Finding: Single interaction point reduces cognitive load
   - Finding: Explicit context mentions improve result quality

5. **Programming Agent UX Studies (2024)**
   - Most effective: Immediate file/code context + natural language
   - Users spend less time on explanation when context is automatic

---

## Conclusion

**Recommended Direction: Hybrid Unified Model**

Your current analysis-focused architecture is valuable and shouldn't be discarded. Instead:

1. **Add** a unified chat input layer (like Copilot)
2. **Keep** specialized panels (your differentiation)
3. **Enable** conversational refinement through follow-ups
4. **Preserve** context across multiple analyses in a session

This approach:
- ✅ Matches industry best practices (Copilot, VS Code, JetBrains)
- ✅ Is backed by UX research
- ✅ Can be implemented incrementally without breaking changes
- ✅ Maintains your specialized visualizations
- ✅ Improves user onboarding and discoverability
- ✅ Enables more sophisticated workflows

**Next Action:** Implement Phase 1 (Session Context Management) to enable future phases without UI changes.

---

**Version:** 1.0  
**Status:** Ready for Review & Implementation Planning  
**Last Updated:** October 27, 2026
