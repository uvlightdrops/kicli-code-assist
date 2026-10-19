# Development Backlog & Ideas

**Purpose:** Internal backlog of suggested features and improvements  
**Created by:** Copilot  
**Last Updated:** 2026-10-19

> This is separate from customer_requests.md which contains only customer input.

---

## High Priority (Foundation)

### Phase A: Logging Infrastructure (3 hours)
**Status:** Planned  
**Why:** Can't debug LLM integration without seeing what's happening

- [ ] Structured logger (file + console)
- [ ] Log file location: configurable
- [ ] Log levels: DEBUG, INFO, WARN, ERROR
- [ ] LLM request logging (provider, URL, prompt, payload)
- [ ] LLM response logging (time, tokens, content)
- [ ] File context logging (load, cache hit/miss)

### Phase B: LLM Integration Testing (2 hours)
**Status:** Planned  
**Why:** Verify AI suggestions actually work before polishing UI

- [ ] Standalone test script
- [ ] Test LLM query with file context
- [ ] Verify hunk generation
- [ ] Test approval workflow
- [ ] Log every step

### Phase C: Remove Broken Features (30 min)
**Status:** Planned  
**Why:** Don't ship things that don't work

- [ ] Diff viewer modal (currently shows empty/crashes)
- [ ] Approval workflow (hunks show 0/X approved)
- [ ] Simplify approval modal (just list + yes/no)
- [ ] Remove visual styling until core works

### Phase D: Context Management (3 hours)
**Status:** Planned  
**Why:** File context is foundation for good AI suggestions

- [ ] Context deduplication (don't load file twice)
- [ ] Context stack visibility
- [ ] File relevance scoring
- [ ] Memory management & warnings

---

## Medium Priority (Polish)

### Tab Clarification
- [ ] Document Terminal tab purpose
- [ ] Document Shell tab purpose
- [ ] Remove if redundant
- [ ] Add help text in UI

### Logging Tab UI
- [ ] Display active logfile path
- [ ] Filter buttons: ERROR / WARN / INFO / DEBUG
- [ ] Auto-scroll to latest
- [ ] Search/grep in logs

### Ghost Text Suggestions (Phase E)
**Status:** Blocked on Phase A-D  
**Why:** Need solid LLM + logging + context first

- [ ] Inline suggestions in editor
- [ ] Gray text styling
- [ ] Accept: Tab or Ctrl+Y
- [ ] Reject: Esc

---

## Low Priority (Future)

### Input Field Enhancements
- [ ] Expand from 1 to 3 lines
- [ ] Command history (Up/Down)
- [ ] Ctrl+Enter send

### File Editor Workflow
- [ ] Preview mode opens in new tab
- [ ] Multiple edit tabs
- [ ] Dirty state tracking
- [ ] Auto-save

### Terminal/Shell Mode
- [ ] Ctrl+X visual improvements
- [ ] Command history
- [ ] Tab completion
- [ ] Environment variables

### Chat History
- [ ] Session organization
- [ ] Search across history
- [ ] Import/export
- [ ] Auto-backup

---

## Known Issues (To Fix)

1. **LLM returns no hunks**
   - "returned no suggestions" message
   - Logs say "Querying LLM..." then silent
   - Root cause unknown (blocked by Phase A logging)

2. **Approval workflow broken**
   - User clicks Approve, counter stays 0/X
   - Unknown if button click reaches handler
   - Unknown if session updates (blocked by logging)

3. **Markup parsing crashes**
   - Code with `[`, `]`, `="..."` crashes renderer
   - Partially fixed with markup=False
   - Need more testing

4. **Tab purposes unclear**
   - What does Terminal tab do?
   - What does Shell tab do?
   - Why are there two?

---

## Architecture Decisions

### Logging Strategy
- **File-based:** Primary (configurable path)
- **Console-based:** Secondary (real-time)
- **TUI-based:** Logging Tab (displays logfile)

### LLM Query Transparency
- Log before/after each LLM call
- Include: Provider, URL, model, prompt, response
- Use structured format (key=value pairs)

### Context Management
- Track loaded files in memory
- Check for duplicates before loading
- Display context stack on demand

---

## Technical Debt

- [ ] Remove hardcoded paths → use config
- [ ] Add type hints to TUI widgets
- [ ] Refactor modal code (lots of duplication)
- [ ] Add tests for AI workflow
- [ ] Document widget hierarchy

---

## Metrics to Track

- [ ] Time: LLM query → response (should be <5s)
- [ ] Size: Context files loaded (should be <10MB)
- [ ] Count: Hunks generated per query (should be 1-5)
- [ ] Rate: Approval success rate (target: >80%)

---

**Next Step:** Start with Phase A (logging infrastructure)  
**Estimated Timeline:** 8 hours total (A-D)  
**Target Date:** 2026-10-19 evening or 2026-10-20 morning
