# Development Roadmap - kicli-code-assist v0.2 to v1.0

## Current Status

**Version**: 0.1 (Foundation Complete) ✅  
**Phase**: 1 - Transition to Phase 2  
**Completion**: 15 of 40 features  
**Code Quality**: All tests passing, 90%+ coverage goal

---

## Feature Hierarchy by Phase

### Phase 1: Foundation ✅ COMPLETE

```
✅ Core TUI Infrastructure
   ✅ File browser with navigation
   ✅ Chat display with scrolling  
   ✅ Multi-line text input
   ✅ 3-mode focus system (B/C/I)
   ✅ Status bar display

✅ Chat & Session Management
   ✅ Chat history persistence
   ✅ Session save/load/resume
   ✅ 5 LLM roles (assistant/architect/debugger/reviewer/explainer)
   ✅ Role-based system prompts
   ✅ Chat export (JSON/Markdown)

✅ Basic File Context
   ✅ Load individual files (L key)
   ✅ Context status display
   ✅ File preview section
   ✅ Unified ki-core configuration
```

**Metrics**:
- Lines of code: 2,500
- Test coverage: 85%
- Tests: 28 passing
- UI responsiveness: <100ms per interaction

---

### Phase 2: Intelligent Context 🔄 IN PROGRESS

**Target**: v0.2 release  
**ETA**: 2-3 weeks  
**Completion**: 0%

```
🔄 Smart File Selection
   ⏳ AST parser for Python/JavaScript/Go
   ⏳ Dependency graph construction  
   ⏳ Import statement analysis
   ⏳ Relevance scoring algorithm
   ⏳ Configuration variables

🔄 Context Caching
   ⏳ Hash-based file caching
   ⏳ LRU eviction policy
   ⏳ Manual invalidation
   ⏳ Cache statistics
   ⏳ TTL configuration

🔄 Context Manager Integration
   ⏳ Ctrl+Shift+L auto-selection
   ⏳ Selection reasoning in chat
   ⏳ File tree display
   ⏳ Context comparison

Configuration Variables:
  context:
    max_files: 10
    max_size_mb: 50
    relevance_threshold: 0.5
    cache_enabled: true
    cache_ttl_hours: 24
    ignore_patterns: [...]
```

**Key Tasks**:
1. [ ] Create `kicli_code_assist/context/smart_selector.py`
2. [ ] Create `kicli_code_assist/context/cache.py`
3. [ ] Add context config to ki-core Config class
4. [ ] Integrate in TUI with Ctrl+Shift+L binding
5. [ ] Write 40+ tests for context subsystem
6. [ ] Document smart selection algorithm

---

### Phase 3: Diff Engine ⏳ PENDING

**Target**: v0.3 release  
**ETA**: 4-5 weeks  
**Completion**: 0%

```
⏳ Diff View Widget
   • Unified diff format display
   • Syntax highlighting by language
   • Line numbers and hunks
   • Navigate between changes
   • Apply/reject buttons
   • Export as patch file

⏳ LLM Output Parsing & File Mapping
   • Extract code blocks from LLM response
   • Parse file path hints
   • Map code to target files
   • Generate unified diffs
   • Validate syntax

⏳ Change Application & Tracking
   • Apply changes to files atomically
   • Create backups automatically
   • Track change history
   • Undo/revert functionality
   • Conflict detection

Configuration Variables:
  diff:
    context_lines: 3
    format: "unified"
    highlight_style: "monokai"
    auto_apply: false
    create_backups: true
    verify_syntax: true

  llm:
    code_block_format: "markdown"
    include_file_paths: true
    strict_mapping: false
    max_context_tokens: 4000
```

**Key Tasks**:
1. [ ] Create `kicli_code_assist/ui/diff_widget.py`
2. [ ] Create `kicli_code_assist/llm/code_extractor.py`
3. [ ] Create `kicli_code_assist/changes/manager.py`
4. [ ] Add diff config to ki-core Config
5. [ ] Integrate diff widget in TUI layout
6. [ ] Write 60+ tests for diff subsystem
7. [ ] Update LLM prompts with examples

---

### Phase 4: GUI Enhancements ⏳ PENDING

**Target**: v0.4 release  
**ETA**: 3-4 weeks  
**Completion**: 0%

```
⏳ Status & Task Display
   • Real-time task status in status bar
   • Task types: analyzing_files, calling_llm, creating_diffs, etc.
   • Progress indicators in chat
   • Timing/duration tracking
   • Task history display

⏳ Feature Hierarchy Display
   • In-app feature browser
   • Completion percentages
   • Nested feature tree
   • Export as markdown
   • Clickable links to docs

Status Bar Enhancement:
  Curr-focus: I  | ✓ 15 files  | ⏳ [Analyzing...] [LLM call...]
```

**Key Tasks**:
1. [ ] Create `kicli_code_assist/ui/status_manager.py`
2. [ ] Create `kicli_code_assist/ui/feature_display.py`
3. [ ] Update status bar widget with task display
4. [ ] Add inline progress to chat messages
5. [ ] Create feature hierarchy data structure
6. [ ] Write 30+ tests for UI subsystem
7. [ ] Design visual indicators (spinners, progress bars)

---

### Phase 5: Advanced Features 📋 PLANNED

**Target**: v1.0 release  
**ETA**: 6-8 weeks  
**Completion**: 0%

```
📋 Multi-File Editing
   • Batch changes across files
   • Atomic multi-file commits
   • Conflict resolution UI
   • Change aggregation

📋 Testing Integration
   • Auto-generate tests for changes
   • Run tests before applying
   • Validate changes against tests
   • Test-driven code generation

📋 Code Review
   • Automatic code quality checks
   • Complexity analysis
   • Security scanning
   • Performance impact analysis

📋 Version Control Integration
   • Diff against git HEAD
   • Create feature branches
   • Commit changes directly
   • Pull request integration

📋 Team Collaboration
   • Shared sessions
   • Comment threads
   • Change reviews
   • Merge conflict resolution
```

---

## Quick Task References

### Highest Priority (Phase 2)

```bash
# Start context system (now)
task: smart-file-selection
  • Implement AST parser
  • Build dependency analyzer  
  • Create relevance scorer
  Depends on: config-migration ✅

task: config-context
  • Add context_* fields to ki-core Config
  • Update ki.yaml.example
  • Document in CONFIG_GUIDE.md
  Depends on: config-migration ✅

task: context-cache
  • Implement cache layer
  • Add cache invalidation
  • Create cache statistics
  Depends on: smart-file-selection
```

### Secondary Priority (Phase 3)

```bash
task: diff-view-widget
  • Create DiffViewer widget
  • Implement syntax highlighting
  • Add navigation controls
  Depends on: context-system

task: file-mapper
  • Parse LLM code blocks
  • Map to target files
  • Generate diffs
  Depends on: llm-prompts-enhance

task: llm-prompts-enhance
  • Create structured prompts
  • Add code generation examples
  • Document prompt format
  Depends on: context-system
```

---

## Configuration Checklist

### Context Configuration (Phase 2)

To implement in ki-core `Config` class:

```python
# Add to Config dataclass
context_max_files: int = 10
context_max_size_mb: int = 50
context_relevance_threshold: float = 0.5
context_cache_enabled: bool = True
context_cache_ttl_hours: int = 24
context_cache_max_size_mb: int = 500
context_ignore_patterns: List[str] = field(default_factory=lambda: [
    "*.pyc", ".git/**", "node_modules/**"
])

# Support in YAML
context:
  max_files: 10
  max_size_mb: 50
  relevance_threshold: 0.5
  cache_enabled: true
  cache_ttl_hours: 24
```

### Diff Configuration (Phase 3)

```python
# Add to Config dataclass
diff_context_lines: int = 3
diff_format: str = "unified"  # unified|side-by-side|inline
diff_highlight_style: str = "monokai"
diff_auto_apply: bool = False
diff_create_backups: bool = True
diff_verify_syntax: bool = True

# Support in YAML
diff:
  context_lines: 3
  format: "unified"
  highlight_style: "monokai"
  auto_apply: false
```

---

## Testing Strategy

### Phase 2 Tests (80+ tests needed)

```python
# tests/test_smart_file_selection.py
- test_ast_parse_python()
- test_ast_parse_javascript()
- test_dependency_graph_construction()
- test_relevance_scoring()
- test_select_top_files()
- test_ignore_patterns()
- test_large_project_performance()

# tests/test_context_cache.py
- test_cache_file()
- test_retrieve_cached_file()
- test_cache_invalidation()
- test_lru_eviction()
- test_cache_statistics()

# tests/test_context_integration.py
- test_full_context_pipeline()
- test_config_overrides()
- test_cache_with_file_changes()
```

### Phase 3 Tests (70+ tests needed)

```python
# tests/test_diff_viewer.py
# tests/test_code_extractor.py
# tests/test_change_manager.py
# tests/test_llm_coordination_pipeline.py
```

---

## File Structure (After Phases 2-4)

```
kicli_code_assist/
├── __init__.py
├── cli.py
├── chat_session.py
│
├── context/                    # Phase 2
│   ├── __init__.py
│   ├── smart_selector.py       # AST parser, dependency analyzer
│   ├── cache.py                # Context caching layer
│   └── analyzer.py             # File analysis utilities
│
├── llm/                        # Phase 3
│   ├── __init__.py
│   ├── code_extractor.py       # LLM output parsing
│   └── prompt_builder.py       # Enhanced prompts
│
├── changes/                    # Phase 3
│   ├── __init__.py
│   ├── manager.py              # Apply/track changes
│   └── backup.py               # Backup handling
│
├── ui/                         # Phases 2-4
│   ├── __init__.py
│   ├── textual_app.py          # Main TUI app
│   ├── diff_widget.py          # Phase 3 - Diff viewer
│   ├── status_manager.py       # Phase 4 - Task display
│   └── feature_display.py      # Phase 4 - Feature hierarchy
│
├── chat_history.py             # ✅ Phase 1
└── prompts.py                  # ✅ Phase 1

tests/
├── test_chat_history_and_prompts.py       # ✅ Phase 1
├── test_smart_file_selection.py           # Phase 2
├── test_context_cache.py                  # Phase 2
├── test_context_integration.py            # Phase 2
├── test_diff_viewer.py                    # Phase 3
├── test_code_extractor.py                 # Phase 3
├── test_change_manager.py                 # Phase 3
├── test_llm_coordination.py               # Phase 3
├── test_status_display.py                 # Phase 4
└── test_integration_full_pipeline.py      # Phase 4

docs/
├── FEATURE_ROADMAP.md                     # Master plan
├── CONFIG_INTEGRATION.md                  # ✅ Phase 1
├── CHAT_HISTORY_AND_PROMPTS.md           # ✅ Phase 1
├── CONTEXT_SYSTEM.md                      # Phase 2
├── DIFF_ENGINE.md                         # Phase 3
├── LLM_COORDINATION.md                    # Phase 3
└── GUI_ENHANCEMENTS.md                    # Phase 4
```

---

## Development Workflow

### For Each Phase:

1. **Planning** (Day 1)
   - [ ] Review FEATURE_ROADMAP.md
   - [ ] Break down into concrete tasks
   - [ ] Update SQL todos with dependencies
   - [ ] Design data structures and APIs

2. **Implementation** (Days 2-5)
   - [ ] Create core module
   - [ ] Implement main classes/functions
   - [ ] Write unit tests
   - [ ] Integrate with existing code

3. **Testing** (Day 6)
   - [ ] Write integration tests
   - [ ] Performance testing
   - [ ] Edge case handling
   - [ ] Manual TUI testing

4. **Documentation** (Day 7)
   - [ ] Create phase documentation
   - [ ] Update README
   - [ ] Add code comments
   - [ ] Document configuration

5. **Review & Polish** (Continuous)
   - [ ] Code review
   - [ ] Refactor if needed
   - [ ] Update DEVELOPMENT.md
   - [ ] Create release notes

---

## Success Criteria by Phase

### Phase 2 Complete When:
- [ ] 80+ tests all passing (including edge cases)
- [ ] Smart file selection works on 5+ project types
- [ ] Context cache shows 50%+ performance improvement
- [ ] Zero memory leaks with large projects
- [ ] All config variables documented
- [ ] Ctrl+Shift+L integrated in TUI

### Phase 3 Complete When:
- [ ] 70+ diff tests passing
- [ ] Diff viewer handles 1000+ line files smoothly
- [ ] LLM output parsing 95%+ accurate
- [ ] File mapping works for Python/JS/Go
- [ ] Change tracking complete with undo
- [ ] Full integration test pipeline passing

### Phase 4 Complete When:
- [ ] Status display shows real-time tasks
- [ ] Feature hierarchy complete and visible
- [ ] All UI widgets responsive (<100ms)
- [ ] Documentation complete
- [ ] User testing feedback incorporated

---

## Known Challenges

### Challenge: Accurate Dependency Analysis
- Different languages, different import systems
- Solution: Language-specific parsers + fallback regex

### Challenge: LLM Output Variability
- LLM responses are unpredictable
- Solution: Structured prompts + flexible parsing + user review

### Challenge: File Conflicts
- Multiple changes to same lines
- Solution: Conflict detection + three-way merge UI

### Challenge: Performance at Scale
- 1000+ file projects are slow
- Solution: Aggressive caching + background processing

---

## Useful Commands

```bash
# Run tests for specific phase
pytest tests/test_smart_file_selection.py -v
pytest tests/test_context_cache.py -v

# Run with coverage
pytest tests/ --cov=kicli_code_assist --cov-report=html

# Check type hints
mypy kicli_code_assist/ --strict

# Run linter
pylint kicli_code_assist/

# Build documentation
cd docs && make html

# Check code quality
radon cc kicli_code_assist/ -a

# Profile performance
py-spy record -o profile.svg -- python -m pytest tests/
```

---

## Contacts & Questions

For questions about:
- **Architecture**: See `docs/FEATURE_ROADMAP.md`
- **Configuration**: See `docs/CONFIG_INTEGRATION.md`
- **Specific features**: See phase documentation in `docs/`
- **Implementation details**: See code docstrings

---

## Release Checklist

### v0.2 (Intelligent Context)
- [ ] All Phase 2 features implemented
- [ ] 80+ tests passing
- [ ] CONFIG_INTEGRATION.md updated
- [ ] User guide for smart file selection
- [ ] Release notes created
- [ ] Version bumped to 0.2.0

### v0.3 (Diff Engine)
- [ ] All Phase 3 features implemented
- [ ] 70+ new tests passing
- [ ] DIFF_ENGINE.md documentation
- [ ] User guide for diff review
- [ ] Performance benchmarks
- [ ] Version bumped to 0.3.0

### v1.0 (Production Ready)
- [ ] All Phase 4 features complete
- [ ] All Phase 5 features planned/started
- [ ] 90%+ test coverage
- [ ] Full documentation
- [ ] Security audit complete
- [ ] Version bumped to 1.0.0

---

**Last Updated**: 2026-09-02  
**Status**: Ready for Phase 2 start  
**Next Step**: Implement smart file selection
