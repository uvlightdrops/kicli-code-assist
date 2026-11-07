---
title: "kicli-code-assist Documentation Audit & Remediation Plan"
project: "kicli-code-assist"
scope: "tracking"
created: 2026-11-01T23:58:00+01:00
updated: 2026-11-01T23:58:00+01:00
update_reason: "Full audit of doc/ directory - 111 files without YAML headers"
status: "active"
author: "Copilot"
---

# kicli-code-assist Documentation Audit & Remediation Plan

## Executive Summary

**Finding:** 111 out of ~112 markdown files in `doc/` **lack YAML headers** and proper metadata. This breaks:
- Machine-readable documentation indexing
- Update tracking & audit trails
- Cross-project documentation linking
- Automated validation

**Impact:** High (docs are unmaintainable at scale)  
**Remediation:** Systematic audit + bulk header addition

---

## Current State (as of 2026-11-01T23:58:00+01:00)

### Compliance Matrix

| Requirement | Compliant | Non-Compliant | Status |
|-------------|-----------|---------------|--------|
| YAML Headers (---) | 1 | 111 | 🔴 CRITICAL |
| Proper Timestamps (ISO 8601 + TZ) | 0 | ~10 | 🔴 CRITICAL |
| Status Field (active/draft/deprecated) | 1 | 111 | 🔴 CRITICAL |
| Clear Scope Field | 0 | 112 | 🔴 CRITICAL |
| Current vs. Vision Separation | ~30% | ~70% | 🟠 HIGH |

### Files Analyzed

```
doc/
├── INDEX.md (no header)
├── README.md (no header)
├── archive/ (23 files, no headers)
├── architecture/ (25 files, no headers)
├── guides/ (8 files, no headers)
├── integration/ (12 files, no headers)
├── phases/ (22 files, 1 with header)
├── tracking/ (3 files, no headers)
└── ...
```

**Total Docs:** ~112 markdown files  
**With Headers:** 1  
**Without Headers:** 111

---

## Problem Categories

### 1. Missing YAML Headers (111 files)

**Examples:**
- `doc/tracking/PROJECT_STATUS.md` - Has `**Date:** 2026-10-19` inline (bad format)
- `doc/phases/PHASE_5_4_SUMMARY.md` - Missing header entirely
- `doc/architecture/AGENT_COORDINATION_ARCHITECTURE.md` - No metadata

**Impact:**
- ❌ Cannot machine-parse document metadata
- ❌ Update tracking impossible
- ❌ Status unknown (is this current or obsolete?)

---

### 2. Bad Timestamp Format (when present)

**Examples:**
```yaml
Date: 2026-10-19           # ❌ No time, no timezone
created: "2026-10-19"      # ❌ Only date
updated: 2026-10-15        # ❌ No timezone
```

**Should be:**
```yaml
created: 2026-11-01T23:58:00+01:00   # ✅ ISO 8601 + timezone
updated: 2026-11-01T23:58:00+01:00   # ✅ With precise hour
```

---

### 3. No Status Field (all 112)

**Problem:** Can't distinguish:
- ✅ Active & current docs
- 📋 Draft docs (in progress)
- 🗂️ Archived but preserved
- ❌ Deprecated (conflicting info)

**Example:** Is `doc/archive/PHASE2_PROJECT_AWARE_CHAT.md` really obsolete, or just old?

---

### 4. Ambiguous Scope (all 112)

**Problem:** Where does each doc fit?
- Architecture decision?
- Phase completion report?
- How-to guide?
- Tracking/status?

**Current Mix:**
```
doc/archive/            ← Implies deprecated, but not marked
doc/architecture/       ← Scope clear
doc/guides/             ← Some guides
doc/phases/             ← Phase reports (unclear if complete)
doc/tracking/           ← Status docs
doc/integration/        ← Some integration plans
```

---

## Remediation Plan

### Phase 1: Quick Audit (1-2 hours)

For each file, determine:
1. **Scope:** `architecture | phases | guides | tracking | integration | archive`
2. **Status:** `active | draft | deprecated | archived`
3. **Last Actual Update:** When was the content last materially changed?

**Tool:** Spreadsheet + git log analysis

```bash
# Get last commit time for each doc
for f in doc/**/*.md; do
  echo "$f: $(git log -1 --format=%aI -- $f)"
done > /tmp/doc_audit.txt
```

---

### Phase 2: Bulk Header Addition (2-3 hours)

**Script Template:**

```python
import os
import yaml
import subprocess
from datetime import datetime

def get_last_commit_time(filepath):
    """Get last commit timestamp for file"""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%aI", "--", filepath],
        capture_output=True, text=True
    )
    return result.stdout.strip() or datetime.now().isoformat()

def add_yaml_header(filepath, scope, status):
    """Add YAML header to markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has header
    if content.startswith('---'):
        return
    
    # Determine title from first heading
    import re
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else os.path.basename(filepath)
    
    last_commit = get_last_commit_time(filepath)
    
    header = f"""---
title: "{title}"
project: "kicli-code-assist"
scope: "{scope}"
created: {last_commit}
updated: {last_commit}
update_reason: "Auto-added YAML header during documentation audit"
status: "{status}"
author: "Copilot"
---

"""
    
    new_content = header + content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ {filepath}")

# Run for all files
for root, dirs, files in os.walk("doc"):
    for f in files:
        if f.endswith(".md"):
            path = os.path.join(root, f)
            
            # Determine scope and status from path
            if "archive" in path:
                scope, status = "archive", "archived"
            elif "phases" in path:
                scope, status = "phases", "active"
            elif "architecture" in path:
                scope, status = "architecture", "active"
            elif "tracking" in path:
                scope, status = "tracking", "active"
            elif "guides" in path:
                scope, status = "guides", "active"
            else:
                scope, status = "misc", "draft"
            
            add_yaml_header(path, scope, status)
```

---

### Phase 3: Manual Verification (2-3 hours)

Check each file for:
- [ ] Correct status (is "archived" file actually obsolete?)
- [ ] Correct scope assignment
- [ ] Title captures essence of doc
- [ ] Any docs that should be merged or cleaned up

**Focus Areas:**
- `doc/archive/` - Should any be un-archived?
- `doc/phases/` - Complete/incomplete phases clearly marked?
- `doc/tracking/` - Up-to-date status info?

---

### Phase 4: Update README & INDEX (30 min)

Create or update `doc/INDEX.md` with YAML header and structured index:

```markdown
---
title: "kicli-code-assist Documentation Index"
project: "kicli-code-assist"
scope: "tracking"
created: 2026-11-01T23:58:00+01:00
updated: 2026-11-01T23:58:00+01:00
status: "active"
---

# Documentation Index

## Architecture (Active)
- [Agent Coordination](./architecture/AGENT_COORDINATION_ARCHITECTURE.md)
- [Phase 4 Architecture](./architecture/PHASE_4_ARCHITECTURE.md)
- ...

## Phases (Completed)
- [Phase 5.4: Full Autonomy](./phases/PHASE_5_4_SUMMARY.md) - Complete
- ...

## Guides
- [Config Validation](./guides/CONFIG_VALIDATION_GUIDE.md)
- ...

## Tracking
- [Project Status](./tracking/PROJECT_STATUS.md)
- [Deployment Readiness](./tracking/DEPLOYMENT_READINESS.md)

## Archive (Deprecated)
- [Phase 2: Project-Aware Chat](./archive/PHASE2_PROJECT_AWARE_CHAT.md)
- ...
```

---

## Known Blockers & Decisions

### Decision: Archive vs. Delete?

**Options:**
- **Option A:** Keep in `archive/` with `deprecated` status → Preserves history
- **Option B:** Delete completely → Cleaner repo

**Recommendation:** Option A (keep but mark deprecated)
- Reason: Git history preserved, but docs clearly marked as outdated
- Prevents re-implementing same mistakes

### Decision: Project Status Update Frequency?

**Current:** `PROJECT_STATUS.md` last updated 2026-10-19 (2 weeks old)

**Recommendation:**
- Update whenever Phase completes
- Add `updated:` timestamp in header
- Keep "Current State" section fresh

---

## Timeline & Ownership

| Phase | Task | Owner | Hours | Deadline |
|-------|------|-------|-------|----------|
| 1 | Audit: scope + status analysis | @uvlightdrops | 2 | 2026-11-02 |
| 2 | Bulk add YAML headers (script) | Copilot | 1 | 2026-11-02 |
| 3 | Manual verification + fixes | @uvlightdrops | 3 | 2026-11-05 |
| 4 | Update INDEX & README | Copilot | 0.5 | 2026-11-05 |
| 5 | Commit & PR | @uvlightdrops | 0.5 | 2026-11-05 |

**Total Effort:** ~7 hours

---

## Definition of Done

- [ ] All 112 `.md` files have YAML headers
- [ ] All timestamps in ISO 8601 + timezone format
- [ ] All files have `status` field (active/draft/deprecated/archived)
- [ ] All files have clear `scope` assignment
- [ ] INDEX.md exists and is comprehensive
- [ ] CI/CD validates YAML headers on commit
- [ ] Zero deprecated docs without clear archival reason

---

## Next Steps

1. **Approve this plan** (scope, timeline, acceptance criteria)
2. **Run audit script** to categorize all files
3. **Bulk add headers** with corrected timestamps
4. **Manual review** + status verification
5. **Commit as single PR:** `docs: add YAML headers and metadata to all doc files`

---