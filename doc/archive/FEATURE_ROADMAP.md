# KI Code Assistant - Feature Roadmap & Architecture

## Executive Summary

This roadmap outlines the evolution of kicli-code-assist from a basic chat interface to a full-featured AI-powered code assistant with intelligent context management, diff visualization, and LLM-coordinated code generation.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    KI Code Assistant                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   UI Layer      │  │ Context Mgmt │  │  LLM Coordination│   │
│  │  ─────────────  │  │  ──────────  │  │  ──────────────  │   │
│  │ • File Browser  │  │• Smart Files │  │• Code Generation│   │
│  │ • Chat Display  │  │• AST Parser  │  │• File Mapping   │   │
│  │ • Diff View     │  │• Dependency  │  │• Diff Creation  │   │
│  │ • Status Bar    │  │  Analysis    │  │• Apply Changes  │   │
│  │ • Task Tracking │  │• Relevance   │  │• Verification   │   │
│  └─────────────────┘  │  Scoring     │  └──────────────────┘   │
│                       │• Caching     │                          │
│                       └──────────────┘                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Configuration System (ki-core Config)                  │   │
│  │  • context_max_files, context_max_size                 │   │
│  │  • diff_context_lines, diff_format                     │   │
│  │  • ignore_patterns, relevance_threshold                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Persistence Layer                                       │   │
│  │  • Chat History + Context Snapshots                     │   │
│  │  • File Analysis Cache                                 │   │
│  │  • Dependency Graphs                                   │   │
│  │  • Applied Changes Log                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    ┌─────────┐         ┌──────────┐         ┌─────────┐
    │ LLM API │         │ File Sys │         │ History │
    │(Ollama/ │         │(Project) │         │  Store  │
    │OpenAI)  │         │          │         │         │
    └─────────┘         └──────────┘         └─────────┘
```

## Phase 1: Foundation ✅ COMPLETE

### 1.1 Core TUI Infrastructure ✅
- [x] File browser with navigation
- [x] Chat display with scrolling
- [x] Multi-line text input with wrapping
- [x] 3-mode focus system (Browser/Chat/Input)
- [x] Status bar with focus/context indicators

### 1.2 Chat & Session Management ✅
- [x] Chat history persistence
- [x] Session save/load/resume
- [x] 5 LLM roles (Code Assistant, Architect, Debugger, Reviewer, Explainer)
- [x] Role-based system prompts
- [x] Unified ki-core configuration system

### 1.3 File Context ✅
- [x] Load individual files (L key)
- [x] Display context status in chat
- [x] Show loaded file count
- [x] File preview section

**Status: 100% Complete - All tests passing, TUI responsive**

---

## Phase 2: Intelligent Context (IN PROGRESS)

### 2.1 Smart File Selection 🔄 PENDING

**Goal**: Automatically select relevant files based on project analysis

**Components**:
```python
# kicli_code_assist/context/smart_selector.py
class SmartFileSelector:
    def analyze_project()      # Scan and categorize files
    def find_related_files()   # Find files related to current context
    def score_relevance()      # Calculate relevance scores
    def select_top_files()     # Select N most relevant files
```

**Features**:
- AST parsing for Python, JavaScript, Go files
- Dependency graph construction
- Import statement analysis
- Function/class reference tracking
- Relevance scoring algorithm:
  - Direct imports: High score
  - Shared dependencies: Medium score
  - Same directory: Low score

**Config Variables**:
```yaml
context:
  max_files: 10              # Maximum files to load
  max_size_mb: 50            # Total context size limit
  ignore_patterns:           # Patterns to exclude
    - "*.pyc"
    - ".git/**"
    - "node_modules/**"
  relevance_threshold: 0.5   # Minimum relevance score
```

**Tests**:
- [ ] Test AST parsing for various languages
- [ ] Test dependency graph construction
- [ ] Test relevance scoring algorithm
- [ ] Test file selection with various project structures

**Dependencies**: `ast`, `pathlib`, existing Config system

---

### 2.2 Context Caching 🔄 PENDING

**Goal**: Cache analyzed files to avoid repeated analysis

**Components**:
```python
# kicli_code_assist/context/cache.py
class ContextCache:
    def analyze_file()         # Parse and cache file info
    def get_cached_info()      # Return cached analysis
    def get_dependency_graph() # Return cached dependency info
    def invalidate_file()      # Invalidate cache when file changes
    def clear_cache()          # Clear all cache
```

**Cache Structure**:
```
$CACHE_DIR/
├── file_analysis/          # File AST + metadata
│   └── <file_hash>.json
├── dependencies/           # Dependency graphs
│   └── <project_hash>.json
├── relevance_scores/       # Pre-computed scores
│   └── <context_hash>.json
└── cache_manifest.json     # Cache metadata & versions
```

**Features**:
- Hash-based file caching
- LRU eviction policy
- Manual cache invalidation
- Cache statistics tracking
- Configurable TTL

**Config Variables**:
```yaml
context:
  cache_enabled: true
  cache_ttl_hours: 24
  cache_max_size_mb: 500
  auto_invalidate: true
```

---

### 2.3 Context Manager Integration 🔄 PENDING

**Goal**: Use smart selector + cache in TUI

**Features**:
- Ctrl+Shift+L: Auto-select relevant files
- Show selection reasoning in chat
- Display loaded file tree
- Track context changes
- Compare contexts between messages

**UI Changes**:
- Add "Auto-Select Files" button in File Browser
- Show file selection explanation
- Display relevance scores
- Highlight selected files

---

## Phase 3: Diff Engine (NOT STARTED)

### 3.1 Diff View Widget 🔄 PENDING

**Goal**: Display file changes in TUI

**Components**:
```python
# kicli_code_assist/ui/diff_widget.py
class DiffViewer(Static):
    def show_diff()           # Display diff between versions
    def highlight_changes()   # Color changed lines
    def show_side_by_side()   # Side-by-side view
    def navigate_changes()    # Jump between hunks
    def get_unified_diff()    # Export as unified diff
```

**Display Format**:
```
┌─ File: src/main.py ─────────────────────────────────────┐
│ @@ -10,5 +10,7 @@                                       │
│  def calculate(x):                                       │
│      result = x * 2                                      │
│ -    return result                                       │
│ +    print(f"Result: {result}")                         │
│ +    return result                                       │
│                                                          │
│ [1/5] ▲ ▼  [Show all changes] [Apply] [Reject]        │
└──────────────────────────────────────────────────────────┘
```

**Features**:
- Syntax highlighting
- Line numbers
- Hunk navigation
- Apply/reject buttons
- Save as patch file

**Config Variables**:
```yaml
diff:
  context_lines: 3           # Lines around change
  format: "unified"          # unified|side-by-side|inline
  highlight_style: "monokai"
  auto_apply: false          # Auto-apply changes
```

---

### 3.2 LLM Output Parsing & File Mapping 🔄 PENDING

**Goal**: Parse LLM responses and map code to files

**Components**:
```python
# kicli_code_assist/llm/code_extractor.py
class LLMCodeExtractor:
    def extract_code_blocks()      # Find ```code``` blocks
    def extract_file_references()  # Find file paths in response
    def map_code_to_files()        # Assign code to target files
    def create_diffs()             # Generate diffs
    def validate_changes()         # Check validity
```

**LLM Prompt Enhancement**:
```
When generating code:
1. Wrap code in ```<language>``` blocks
2. Include target file path: ```python:src/main.py
3. Use clear markers:
   - [INSERT at line 42]
   - [REPLACE lines 10-15]
   - [DELETE lines 5-8]
4. Provide reasoning for changes
```

**Example LLM Response**:
```
I'll refactor your code:

```python:src/utils.py [INSERT at end]
def calculate_total(items):
    """Calculate sum of items."""
    return sum(item.value for item in items)
```

```javascript:app.js [REPLACE lines 15-20]
function handleSubmit(data) {
    const result = await api.post('/submit', data);
    return result.json();
}
```

This adds a utility function and updates the handler.
```

---

### 3.3 Change Application & Tracking 🔄 PENDING

**Goal**: Apply changes to files and track history

**Components**:
```python
# kicli_code_assist/changes/manager.py
class ChangeManager:
    def apply_change()         # Write change to file
    def create_backup()        # Backup before change
    def track_change()         # Log change in history
    def revert_change()        # Undo change
    def get_change_log()       # Show all changes
    def export_changes()       # Export as patch
```

**Features**:
- Atomic file operations
- Automatic backups in `.kicli-backups/`
- Change history with timestamps
- Undo/redo functionality
- Conflict detection
- Change verification

**Change Log Format**:
```json
{
  "timestamp": "2026-09-02T12:00:00Z",
  "file": "src/main.py",
  "type": "INSERT|REPLACE|DELETE",
  "lines": [10, 15],
  "content_before": "...",
  "content_after": "...",
  "llm_session": "session-123",
  "applied": true,
  "reverted": false
}
```

---

## Phase 4: GUI Enhancements (NOT STARTED)

### 4.1 Status & Task Display 🔄 PENDING

**Goal**: Show real-time processing status

**Components**:
```python
# kicli_code_assist/ui/status_manager.py
class StatusManager:
    def add_task()            # Register active task
    def update_task()         # Update task progress
    def complete_task()       # Mark task done
    def get_active_tasks()    # List running tasks
    def format_status()       # Format for display
```

**Status Bar Enhancement**:
```
Curr-focus: I  | ✓ Project loaded (15 files)  |  ⏳ [Analyzing files...] [LLM call...]
```

**Chat Integration**:
```
You: Refactor the authentication module

🤖 Assistant: I'll refactor the authentication module.
    ⏳ Analyzing project...  (2.3s)
    ⏳ Finding related files...  (1.1s)  
    ⏳ Loading context...  (0.8s)
    ⏳ Calling LLM...  (3.2s)
    ✓ Generated code
    ⏳ Creating diffs...  (0.5s)
    ✓ Found 3 file changes

Here are the changes:
```

**Task Types**:
- `analyzing_files`: AST parsing in progress
- `loading_context`: Reading files
- `scoring_files`: Relevance calculation
- `calling_llm`: LLM API request
- `parsing_response`: Extracting code blocks
- `creating_diffs`: Generating unified diffs
- `applying_changes`: Writing to files

---

### 4.2 Feature Hierarchy Display 🔄 PENDING

**Goal**: Show all features with completion status

**Components**:
```python
# kicli_code_assist/ui/feature_display.py
class FeatureHierarchy:
    def get_feature_tree()    # Get nested feature list
    def get_completion_stats()# Get completion percentages
    def display_tree()        # Format for display
    def export_markdown()     # Export as markdown
```

**In-App Display**:
```
Press '?' to see features

╭─ Context Management (60% complete)
│ ├─ Smart File Selection (0%)
│ ├─ Context Caching (0%)
│ ├─ Dependency Analysis (0%)
│ └─ Relevance Scoring (0%)
│
├─ Diff Engine (0% complete)
│ ├─ Diff Viewer (0%)
│ ├─ LLM Output Parsing (0%)
│ └─ Change Application (0%)
│
├─ LLM Coordination (0% complete)
│ ├─ Enhanced Prompts (0%)
│ ├─ Code Extraction (0%)
│ └─ File Mapping (0%)
│
└─ Configuration (100% complete)
  ├─ Unified Config System ✓
  ├─ Context Config (0%)
  └─ Diff Config (0%)
```

---

## Phase 5: Advanced Features (FUTURE)

### 5.1 Multi-File Editing
- Batch changes across files
- Atomic multi-file commits
- Conflict resolution
- Change aggregation

### 5.2 Testing Integration
- Auto-generate tests for changes
- Run tests before applying
- Validate changes against tests
- Test-driven code generation

### 5.3 Code Review
- Automatic code quality checks
- Complexity analysis
- Security scanning
- Performance impact analysis

### 5.4 Version Control Integration
- Diff against git HEAD
- Create feature branches
- Commit changes directly
- Pull request integration

### 5.5 Team Collaboration
- Shared sessions
- Comment threads
- Change reviews
- Merge conflict resolution

---

## Configuration Reference

### Context Configuration
```yaml
context:
  # File selection
  max_files: 10
  max_size_mb: 50
  relevance_threshold: 0.5
  
  # Analysis
  analyze_imports: true
  analyze_dependencies: true
  include_test_files: false
  
  # Caching
  cache_enabled: true
  cache_ttl_hours: 24
  cache_max_size_mb: 500
  
  # Patterns
  ignore_patterns:
    - "*.pyc"
    - ".git/**"
    - "node_modules/**"
    - ".pytest_cache/**"
```

### Diff Configuration
```yaml
diff:
  # Display
  context_lines: 3
  format: "unified"  # unified|side-by-side|inline
  highlight_style: "monokai"
  
  # Application
  auto_apply: false
  create_backups: true
  backup_dir: ".kicli-backups"
  
  # Validation
  verify_syntax: true
  run_linter: false
  warn_on_conflict: true
```

### LLM Coordination Configuration
```yaml
llm:
  # Code generation
  code_block_format: "markdown"  # markdown|xml|custom
  include_line_numbers: true
  include_file_paths: true
  
  # Change mapping
  strict_mapping: false
  auto_merge_close_hunks: true
  max_context_tokens: 4000
  
  # Verification
  check_syntax_after_generation: true
  run_tests_after_apply: false
```

---

## Implementation Timeline

### Week 1: Smart File Selection
- [ ] AST parser for Python/JavaScript
- [ ] Dependency analyzer
- [ ] Relevance scoring algorithm
- [ ] Tests for all components

### Week 2: Context Caching & Integration
- [ ] Cache layer implementation
- [ ] Cache invalidation logic
- [ ] UI integration (Ctrl+Shift+L)
- [ ] Tests and performance benchmarks

### Week 3: Diff Engine
- [ ] Diff viewer widget
- [ ] LLM output parser
- [ ] File mapper
- [ ] UI integration and tests

### Week 4: Change Application & Status Display
- [ ] Change manager
- [ ] File application logic
- [ ] Status display
- [ ] Task tracking UI

### Week 5+: Refinement & Advanced Features
- [ ] Performance optimization
- [ ] Edge case handling
- [ ] User testing
- [ ] Documentation

---

## Success Metrics

### Code Quality
- [ ] 90%+ test coverage
- [ ] All type hints in place
- [ ] Zero security warnings
- [ ] Performance: <500ms for file selection on 1000-file project

### User Experience
- [ ] Sub-second UI responsiveness
- [ ] Clear error messages
- [ ] Intuitive keyboard navigation
- [ ] Helpful documentation

### Feature Completeness
- [ ] All planned Phase 2-4 features implemented
- [ ] Full Phase 5 feature set planned (even if not all implemented)
- [ ] Comprehensive configuration options
- [ ] Solid integration tests

---

## Testing Strategy

### Unit Tests
- Smart file selection logic
- Relevance scoring
- AST parsing
- Diff generation
- Change application

### Integration Tests
- Full pipeline: files → analysis → LLM → diff → apply
- Multi-file changes
- Config overrides
- Cache invalidation

### UI Tests
- Diff viewer widget
- Status display updates
- Task tracking
- Focus management with new widgets

### Performance Tests
- Large project handling (1000+ files)
- Memory usage under load
- Cache effectiveness
- LLM response parsing speed

---

## Documentation TODO

- [ ] User guide: Smart file selection
- [ ] User guide: Reviewing and applying diffs
- [ ] User guide: Configuration options
- [ ] API docs: Context manager
- [ ] API docs: Diff engine
- [ ] API docs: Change manager
- [ ] Architecture docs: LLM coordination
- [ ] Troubleshooting: Common issues

---

## Known Challenges & Solutions

### Challenge 1: Accurate Dependency Analysis
**Problem**: Different languages have different import systems
**Solution**: 
- Language-specific parsers
- Fallback to regex-based detection
- User hints for non-standard imports
- Cached results for performance

### Challenge 2: LLM Output Parsing
**Problem**: LLM responses are unpredictable
**Solution**:
- Structured prompt templates
- Example-based prompting
- Flexible parsing with heuristics
- User review before applying

### Challenge 3: File Conflicts
**Problem**: Multiple changes to same lines
**Solution**:
- Conflict detection algorithm
- User intervention with merge UI
- Three-way merge support
- Undo/revert functionality

### Challenge 4: Performance
**Problem**: Large file analysis is slow
**Solution**:
- Aggressive caching
- Incremental analysis
- Background processing
- Configurable limits

---

## Glossary

| Term | Definition |
|------|------------|
| **Context** | Set of files loaded for LLM awareness |
| **Relevance Score** | Numeric value indicating file importance to current task |
| **Hunk** | A section of changed lines in a diff |
| **Change** | Individual file modification (insert/replace/delete) |
| **Diff** | Structured representation of changes |
| **AST** | Abstract Syntax Tree - parsed code structure |
| **Dependency Graph** | Network of file imports and relationships |

---

## Version History

- **v0.1** (Current): Foundation complete, Phase 1 ✅
- **v0.2** (Next): Smart context, Phase 2
- **v0.3** (Future): Diff engine, Phase 3
- **v0.4** (Future): Advanced coordination, Phase 4-5
- **v1.0** (Goal): Full-featured production-ready assistant

