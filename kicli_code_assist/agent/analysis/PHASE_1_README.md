# Phase 1: Minimal Analysis Components 🚀

**Status:** Bare-bones, ready for fast iteration

## What's Here (500 lines, not 1500!)

1. **ASTAnalyzer** - Parse Python syntax trees
   - Functions, classes, imports extraction
   - Docstring & complexity calculation
   - ~300 lines

2. **DependencyResolver** - Quick import tracking
   - Find files that import this file
   - Impact analysis (what breaks if we change this?)
   - ~50 lines (heuristic-based, not perfect)

3. **ProjectAnalysisService** - Detect project type
   - Find frameworks (Flask, Django, FastAPI)
   - Find entry points (main.py, app.py)
   - ~40 lines (simple grep-based)

4. **SemanticIndexer** - In-memory search cache
   - Index functions and their summaries
   - Search by name/summary
   - ~30 lines (dict-based, no SQLite yet)

5. **SmartSelector** - Token-aware context picker
   - Select code snippets within token budget
   - Estimate tokens (rough formula)
   - ~40 lines (greedy approach, no ranking yet)

## Design Philosophy

✅ **Minimal:** Only essentials, no over-engineering
✅ **Fast:** Heuristics over perfect algorithms
✅ **Iterative:** Easy to refactor based on real usage
✅ **Testable:** Each component has clear inputs/outputs

## Known Limitations (by design)

- DependencyResolver uses simple string matching, not AST
- ProjectAnalysisService only checks common filenames
- SemanticIndexer is in-memory (not persistent)
- SmartSelector doesn't rank by relevance (yet)

## Integration Points

These components are meant to be used by:
- `/api/agent/explain` - Explain selected code
- `/api/agent/suggest` - Suggest refactorings
- Agent reasoning layer (Phase 2)

## Example Usage

```python
from kicli_code_assist.agent.analysis import ASTAnalyzer, DependencyResolver

# Analyze a file
analyzer = ASTAnalyzer()
functions, classes, imports = analyzer.analyze_file(Path("main.py"))

# Get impact of changes
resolver = DependencyResolver(Path("."))
impact = resolver.get_impact(Path("utils.py"))
```

## Phase 1 → Phase 2 Improvements

- Add proper AST-based dependency resolution
- Persistent SQLite indexing
- LLM-based relevance ranking for SmartSelector
- Circular dependency detection
- Multi-language support (JS/TS)

---

**Keep it simple. Ship fast. Iterate based on feedback.**
