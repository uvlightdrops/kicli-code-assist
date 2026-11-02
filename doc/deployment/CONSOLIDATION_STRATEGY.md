---
title: "Deployment Documentation Consolidation Strategy"
project: "kicli-code-assist"
scope: "documentation"
created: 2026-11-02T04:12:00+01:00
updated: 2026-11-02T04:12:00+01:00
update_reason: "Analyze duplicated docs across repos and create consolidation plan"
status: "analysis"
agent_project: "kicli-code-assist"
author: "Copilot"
---

# Deployment Documentation Consolidation Analysis

## Problem Statement

Deployment configuration and documentation is duplicated across 4+ locations:

1. **kicli-code-assist** `/doc/deployment/` (8 files, 600+ lines)
2. **stackctl** `/doc/` (2 files)
3. **dev_doc** (no dedicated deployment section)
4. **ki-ecosystem** `/config/defaults/stack.yaml` (reference)

Each repo maintains partial copies of the same information, causing:
- Inconsistency when one doc is updated
- Confusion about source of truth
- Maintenance burden across repos
- Missing cross-project context

---

## Current State Analysis

### kicli-code-assist `/doc/deployment/`

| File | Purpose | Status | Issues |
|------|---------|--------|--------|
| README.md | Symlink deployment intro | ⚠️ Outdated | Mentions make prod-update |
| CURRENT_STATUS.md | Dev/prod stage config | 🟡 Partial | No YAML headers, duplicates stackctl docs |
| STACKCTL_STATUS.md | Config merge semantics | 🟡 Partial | Overlaps with stackctl/doc/README.md |
| STACKCTL_ARCHITECTURE.md | Design rationale | ✅ Good | Self-contained |
| STACKCTL_IMPLEMENTATION.md | Usage guide | ✅ Good | Self-contained |
| STACK_YAML_VARIANTS.md | Stage examples | ✅ Good | Self-contained |
| SEMI_PROD_DEPLOYMENT.md | Alternative approach | ❓ Unclear | Dated proposal |
| OPTION2_SYSTEMD.md | Systemd integration | ❓ Unclear | Dated proposal |

### stackctl `/doc/`

| File | Purpose | Status |
|------|---------|--------|
| README.md | Project-local stackctl usage | ✅ Canonical | Shared across all projects |
| CONSISTENCY_REPORT.md | Audit of installations | ✅ Canonical | One-time snapshot |

### dev_doc

**No dedicated deployment section.**
- Exists: yaml_config_administration.md (general, not deployment-specific)
- Missing: Centralized deployment architecture
- Missing: Stage selection criteria
- Missing: Cross-project deployment patterns

---

## Overlapping Content

### Content Found in Multiple Places

| Content | Locations | Should Be In |
|---------|-----------|--------------|
| Project-local stackctl usage | kicli-code-assist + stackctl/doc | **stackctl/doc/README.md** |
| KI_STAGE environment variable | CURRENT_STATUS.md + STACKCTL_STATUS.md | **Either doc, with cross-ref** |
| Stage merge semantics | STACKCTL_STATUS.md + stackctl/doc | **stackctl/doc or ki_core** |
| Config loader pattern | Multiple deployment docs | **dev_doc or ki_core docs** |
| Service definitions (stack.yaml) | kicli-code-assist + ki-ecosystem | **Project defaults only** |

---

## Proposed Consolidation

### Tier 1: Canonical Sources (No Duplication)

**stackctl/doc/README.md**
- ✅ Project-local stackctl usage (already canonical)
- ✅ .venv/bin/python -m stackctl pattern
- ✅ Environment variable precedence
- **Add needed:** Quick start examples per project

**dev_doc/**
- ✅ Cross-project deployment patterns
- **Add needed:** Stage selection criteria
- **Add needed:** Config loader architecture
- **Add needed:** Troubleshooting guide

**kicli-code-assist/config/defaults/stack.yaml + config/stages/**
- ✅ Project-specific service definitions
- **Add needed:** YAML headers with schema version

### Tier 2: Project-Specific Docs (With Cross-References)

**kicli-code-assist/doc/deployment/**

Keep only:
- `STACKCTL_ARCHITECTURE.md` - Why stackctl for this project
- `STACKCTL_IMPLEMENTATION.md` - Project-specific setup guide
- `STACK_YAML_VARIANTS.md` - Project stage examples
- **Remove:** Duplicates of general usage (reference stackctl/doc instead)
- **Remove:** CURRENT_STATUS.md, STACKCTL_STATUS.md (merge into README)
- **Add:** `README.md` with:
  - Quick start (reference stackctl/doc)
  - Project context
  - Links to dev_doc patterns

### Tier 3: Archive/Deprecate

- `README.md` (outdated symlink reference)
- `SEMI_PROD_DEPLOYMENT.md` (proposal, not current)
- `OPTION2_SYSTEMD.md` (proposal, not current)

---

## YAML Header Standards

### For kicli-code-assist Deployment Docs

```yaml
---
title: "Descriptive Title"
project: "kicli-code-assist"
agent_project: "kicli-code-assist"  # Who originally created this doc
scope: "deployment"  # sub-scope: "configuration" | "architecture" | "troubleshooting"
purpose: "What problem does this doc solve?"
created: YYYY-MM-DDTHH:MM:SS+01:00
updated: YYYY-MM-DDTHH:MM:SS+01:00
update_reason: "Why was it updated?"
status: "active" | "deprecated" | "proposal" | "archived"
cross_references:
  - "stackctl/doc/README.md (Project-local usage)"
  - "dev_doc/DEPLOYMENT_STANDARDS.md (Cross-project patterns)"
  - "ki_core/docs/config.md (Config merge semantics)"
---
```

---

## Recommended Actions

### Phase 1: Create Canonical Sources (Priority 1)

**dev_doc/DEPLOYMENT_STANDARDS.md** (NEW)
- Cross-project deployment architecture
- Stage selection criteria (development, staging, production)
- Config loader pattern (stackctl + ki_core)
- Environment variable precedence
- Troubleshooting guide
- **Purpose:** Single source of truth for all KI projects

**stackctl/doc/README.md** (ENHANCE)
- ✅ Keep project-local usage (already good)
- **Add:** Quick start examples for kicli-code-assist
- **Add:** Links to dev_doc for cross-project context
- **Status:** Canonical for "How to use stackctl"

### Phase 2: Consolidate kicli-code-assist Docs

1. **kicli-code-assist/doc/deployment/README.md** (REWRITE)
   - Remove duplicated general info
   - Add YAML header
   - Add cross-references
   - Keep: project-specific context

2. **CURRENT_STATUS.md & STACKCTL_STATUS.md** (MERGE)
   - Create single status tracking file
   - Add YAML headers
   - Reference canonical sources instead of duplicating

3. **Archive:**
   - Move SEMI_PROD_DEPLOYMENT.md → archive/
   - Move OPTION2_SYSTEMD.md → archive/
   - Keep for reference only

### Phase 3: Add Missing Documentation

**ki_core** (Or reference in dev_doc)
- Config merge semantics (currently under-documented)
- active_layers() usage
- KI_STAGE vs profiles distinction

**dev_doc**
- Operator runbook
- Troubleshooting matrix
- Performance tuning

---

## Header Integration Plan

### Immediate (This Session)

Apply YAML headers to existing files:
- kicli-code-assist/doc/deployment/*.md
- stackctl/doc/*.md

### During Consolidation

- All new files get headers
- Rewritten files get updated headers
- Archive entries get deprecated status

### Going Forward

- All documentation in dev_doc must have headers
- All project-specific docs should cross-reference
- Headers should indicate "canonical" vs "reference" status

---

## Cross-Reference Pattern

### Example: When to Reference vs Copy

❌ **Don't copy:**
```
See stackctl/doc/README.md for how to use stackctl in your project.
```

✅ **Do this:**
```yaml
---
title: "Deployment Setup for kicli-code-assist"
cross_references:
  - "stackctl/doc/README.md: Project-local usage pattern"
  - "dev_doc/DEPLOYMENT_STANDARDS.md: Cross-project context"
---

# Deployment Setup

For general stackctl usage, see [stackctl/doc/README.md](../../stackctl/doc/README.md).
This guide focuses on kicli-code-assist specific configuration.
```

---

## Storage Locations (Final State)

### Canonical Sources

```
dev_doc/
├── DEPLOYMENT_STANDARDS.md (NEW - Cross-project)
├── yaml_config_administration.md (Enhanced - Config management)
└── architecture/
    └── DEPLOYMENT_ARCHITECTURE.md (NEW - System design)

stackctl/doc/
├── README.md (Enhanced - Canonical local usage)
└── CONSISTENCY_REPORT.md (Periodically updated)
```

### Project-Specific

```
kicli-code-assist/doc/deployment/
├── README.md (Rewritten - project context + cross-refs)
├── STACKCTL_ARCHITECTURE.md (Keep - project rationale)
├── STACKCTL_IMPLEMENTATION.md (Keep - project setup)
├── STACK_YAML_VARIANTS.md (Keep - project examples)
└── STATUS.md (NEW - project progress)

ki-ecosystem/
├── doc/INTEGRATION.md (NEW - How projects interconnect)
└── config/defaults/stack.yaml (Reference only)
```

### Archive

```
kicli-code-assist/doc/deployment/archive/
├── SEMI_PROD_DEPLOYMENT.md (Dated proposal)
├── OPTION2_SYSTEMD.md (Dated proposal)
└── CURRENT_STATUS.md (Merged into STATUS.md)
```

---

## Benefits of Consolidation

1. **Single Source of Truth**
   - Changes to deployment process need only update dev_doc
   - Project docs reference canonical source

2. **Reduced Maintenance**
   - No more syncing duplicate info across repos
   - YAML headers track who last touched what

3. **Better Discovery**
   - Cross-references help operators find related info
   - Clearer which doc to read for specific questions

4. **Consistency Across Projects**
   - All KI projects follow same deployment patterns
   - dev_doc becomes ecosystem standards

5. **Historical Tracking**
   - YAML headers show evolution
   - Archive keeps proposals for reference

---

## Implementation Sequence

### Session 1: Create Headers & Analysis (This One)
- [ ] Add YAML headers to all deployment docs
- [ ] Create this consolidation strategy doc
- [ ] Document duplication matrix

### Session 2: Create Canonical Sources
- [ ] Create dev_doc/DEPLOYMENT_STANDARDS.md
- [ ] Enhance stackctl/doc/README.md
- [ ] Add cross-references

### Session 3: Consolidate Project Docs
- [ ] Rewrite kicli-code-assist/doc/deployment/README.md
- [ ] Merge CURRENT_STATUS.md + STACKCTL_STATUS.md
- [ ] Archive outdated docs

### Session 4: Implement in Other Projects
- [ ] Apply pattern to ki-knowledge
- [ ] Apply pattern to ki-ecosystem
- [ ] Verify consistency

---

## Questions for User

1. **Canonical Location:** Should deployment standards live in:
   - `dev_doc/DEPLOYMENT_STANDARDS.md` (recommended)
   - `ki-core/docs/DEPLOYMENT.md` (alternative)
   - Both with cross-reference? ✅

2. **Stage Naming:** Should cross-project stages be standardized?
   - `development` | `staging` | `production` (recommended)
   - Per-project variation allowed?

3. **Archive Strategy:** Keep outdated proposals in repo?
   - Yes, in `doc/deployment/archive/` (recommended)
   - No, delete completely?
   - Move to separate archive branch?

---

**Analysis Complete:** 2026-11-02T04:12:00+01:00  
**Recommendation:** Proceed with consolidation plan  
**Next:** Implement Phase 1 (Create canonical sources)
