# Phase 2D API Guide: /api/agent/route

Quick reference for frontend integration.

## Endpoint

```
POST /api/agent/route
```

## Quick Example

```javascript
// Basic usage
const response = await fetch('http://localhost:8000/api/agent/route', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "Explain this function and show metrics",
    file_path: "src/utils.py",
    project_root: "/home/user/myproject"
  })
});

const data = await response.json();

if (data.success) {
  console.log(`Intent: ${data.intent.type}`);
  console.log(`Confidence: ${(data.intent.confidence * 100).toFixed(1)}%`);
  
  // Render tabs dynamically
  Object.entries(data.tabs).forEach(([name, content]) => {
    console.log(`Tab: ${name}`);
    console.log(content.content);
  });
}
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ YES | Natural language query (e.g., "Explain this code") |
| `file_path` | string | ✅ YES | Path to file (relative or absolute) |
| `project_root` | string | ❌ NO | Project root directory (inferred if not provided) |
| `scope` | string | ❌ NO | "folder" (default) or "project" |
| `session_id` | string | ❌ NO | Session UUID (auto-generated if omitted) |

## Response (Success: 200)

```json
{
  "success": true,
  "session_id": "abc-123-def-456",
  
  "query": "Explain this function",
  
  "intent": {
    "type": "explain",           // "explain", "optimize", "refactor", etc.
    "confidence": 0.95,          // 0.0 to 1.0
    "agents": ["explain", "metrics"],
    "reasoning": "Query contains 'explain' keyword..."
  },
  
  "summary": "This is a utility function...",
  
  "tabs": {
    "Structure": {
      "title": "Structure",
      "content": "File structure and organization...",
      "metadata": { "functions": 5, "classes": 2 }
    },
    "Metrics": {
      "title": "Metrics",
      "content": "Lines of code, complexity...",
      "metadata": { "loc": 150, "complexity": 8 }
    }
  },
  
  "actions": [
    {
      "action_type": "write_file",
      "target": "myfile.py",
      "description": "Add type hints",
      "details": { "line": 42, "suggestion": "def foo(x: int) -> str:" },
      "priority": "medium"
    }
  ],
  
  "next_steps": [
    "Add type hints",
    "Reduce function complexity",
    "Add docstrings"
  ],
  
  "timing": {
    "intent_ms": 1.2,
    "execution_ms": 350.0,
    "aggregation_ms": 150.0,
    "total_ms": 501.2
  },
  
  "synthesis_method": "llm"  // "llm" or "template"
}
```

## Response (Error)

### HTTP 400 - Bad Request
```json
{
  "success": false,
  "error": "Missing 'file_path' parameter",
  "session_id": "abc-123-def-456"
}
```

### HTTP 403 - Access Denied
```json
{
  "success": false,
  "error": "Access denied: file outside project",
  "session_id": "abc-123-def-456"
}
```

### HTTP 500 - Server Error
```json
{
  "success": false,
  "error": "Error details here",
  "session_id": "abc-123-def-456"
}
```

## Intent Types

| Type | When Used | Agents |
|------|-----------|--------|
| `explain` | "Explain", "How does", "What is" | explain, metrics |
| `optimize` | "Optimize", "Performance", "Speed up" | metrics, refactor |
| `refactor` | "Refactor", "Improve", "Clean up" | refactor, suggest |
| `diagnose` | "Debug", "Error", "Fix" | explain, metrics, dependencies |
| `review` | "Review", "Check", "Audit" | review, suggest |
| `suggest` | "Suggest", "Recommend" | suggest, metrics |
| `validate` | "Validate", "Check dependencies" | review, dependencies |

## Confidence Score Interpretation

| Range | Meaning |
|-------|---------|
| 0.75-1.0 | Very confident (reliable intent) |
| 0.5-0.74 | Somewhat confident (likely correct) |
| 0.0-0.49 | Low confidence (may be inaccurate) |

## Tab Content Structure

Each tab in the response has this structure:

```json
{
  "title": "Structure",
  "content": "Main content as string or HTML",
  "metadata": {
    "functions": 5,
    "classes": 2,
    "imports": 8
  }
}
```

Common tab names:
- `Structure` - File structure, functions, classes
- `Metrics` - Code metrics, LOC, complexity
- `Refactor` - Refactoring suggestions
- `Dependencies` - Dependency analysis
- `Review` - Code review findings

## Action Types

```json
{
  "action_type": "write_file",     // "write_file", "modify_file", "create_directory"
  "target": "filename.py",          // File or directory path
  "description": "Add type hints",  // Human-readable description
  "details": {...},                 // Action-specific data
  "priority": "medium"              // "low", "medium", "high"
}
```

## Error Handling Best Practices

```javascript
// Handle different error types
async function analyzeCode(query, filePath) {
  try {
    const response = await fetch('http://localhost:8000/api/agent/route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, file_path: filePath })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      // Handle error response
      if (response.status === 400) {
        console.error('Invalid parameters:', data.error);
        // Show validation error to user
      } else if (response.status === 403) {
        console.error('Access denied:', data.error);
        // Show access error
      } else if (response.status === 500) {
        console.error('Server error:', data.error);
        // Show server error
      }
      return null;
    }
    
    return data;
    
  } catch (error) {
    console.error('Network error:', error);
    // Show network error to user
  }
}
```

## Performance Notes

- **Total time**: 500-600ms (typical)
- **Intent detection**: <2ms (LLM with fast fallback)
- **Agent execution**: 350-400ms (parallel)
- **Aggregation**: 150-200ms (LLM synthesis)

For performance monitoring:
- Track `data.timing.total_ms`
- Monitor `data.timing.execution_ms` for agent performance
- Alert if total exceeds 2000ms

## Session Tracking

```javascript
// First request - auto-generated session
const response1 = await fetch('http://localhost:8000/api/agent/route', {
  method: 'POST',
  body: JSON.stringify({
    query: "Explain this function",
    file_path: "utils.py"
  })
});
const sessionId = response1.json().session_id;

// Follow-up with same session
const response2 = await fetch('http://localhost:8000/api/agent/route', {
  method: 'POST',
  body: JSON.stringify({
    query: "Show me more details about the return type",
    file_path: "utils.py",
    session_id: sessionId
  })
});
```

## Synthesis Method

The response includes `synthesis_method` to indicate how results were generated:

- `"llm"` - Synthesized using OpenAI (higher quality)
- `"template"` - Fallback template-based synthesis (if LLM unavailable)

Use this for:
- Analytics (track LLM availability)
- User indication (show "AI-powered" vs "analysis")
- Fallback handling

## TypeScript Types (Optional)

```typescript
interface AgentRouteRequest {
  query: string;
  file_path: string;
  project_root?: string;
  scope?: "folder" | "project";
  session_id?: string;
}

interface AgentIntent {
  type: string;
  confidence: number;
  agents: string[];
  reasoning: string;
}

interface TabContent {
  title: string;
  content: string;
  metadata: Record<string, any>;
}

interface Action {
  action_type: "write_file" | "modify_file" | "create_directory";
  target: string;
  description: string;
  details: Record<string, any>;
  priority: "low" | "medium" | "high";
}

interface Timing {
  intent_ms: number;
  execution_ms: number;
  aggregation_ms: number;
  total_ms: number;
}

interface AgentRouteResponse {
  success: boolean;
  session_id: string;
  query: string;
  intent: AgentIntent;
  summary: string;
  tabs: Record<string, TabContent>;
  actions: Action[];
  next_steps: string[];
  timing: Timing;
  synthesis_method: "llm" | "template";
  error?: string;  // Only in error responses
}
```

## Common Queries

```
"Explain this file"
→ Returns Structure and Metrics tabs

"What can I optimize here?"
→ Returns Metrics and Refactor tabs with suggestions

"Show me dependencies"
→ Returns Dependencies tab

"Is this code well-written?"
→ Returns Review and Suggestions tabs

"How complex is this?"
→ Returns Metrics with complexity scores

"Add type hints"
→ Returns Refactor tab with type hint suggestions
```

## Debugging Tips

```javascript
// Log full response for debugging
console.log(JSON.stringify(data, null, 2));

// Monitor timing breakdown
console.group('Timing');
console.log(`Intent: ${data.timing.intent_ms}ms`);
console.log(`Execution: ${data.timing.execution_ms}ms`);
console.log(`Aggregation: ${data.timing.aggregation_ms}ms`);
console.log(`Total: ${data.timing.total_ms}ms`);
console.groupEnd();

// Check intent confidence
if (data.intent.confidence < 0.7) {
  console.warn('Low confidence intent - results may be inaccurate');
}

// Verify synthesis method
if (data.synthesis_method === 'template') {
  console.info('Using template-based synthesis (LLM unavailable)');
}
```

## Migration from Phase 1

**Phase 1 (Old)**: Multiple endpoint calls
```javascript
const explain = await fetch('/api/agent/explain', {...});
const metrics = await fetch('/api/agent/metrics', {...});
const refactor = await fetch('/api/agent/refactor', {...});
```

**Phase 2D (New)**: Single endpoint call
```javascript
const result = await fetch('/api/agent/route', {
  body: JSON.stringify({
    query: "Explain and optimize this code",
    file_path: "utils.py"
  })
});
```

**Benefits**:
- 50% fewer network requests
- 57% faster response (1.5-2.7x speedup)
- Single response with all data
- Consistent error handling

---

For more details, see: `doc/phases/PHASE_2D_IMPLEMENTATION.md`
