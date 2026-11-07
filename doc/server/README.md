---
title: Server Management & Orchestration
project: kicli-code-assist
scope: Deployment & Service Control
status: active
created: 2026-11-05T23:40:00+01:00
updated: 2026-11-05T23:40:00+01:00
update_reason: Consolidated with SERVICE_ORCHESTRATION_PATTERN in ~/dev_doc; removed historical server_management design (Oct 28) in favor of stackctl-based approach
agent_project: Service orchestration, deployment
cross_references:
  - ~/dev_doc/SERVICE_ORCHESTRATION_PATTERN.md (current: stackctl + Layer 1 design)
  - ~/dev_doc/server-mngm/ (historical: Oct 28 design, not implemented)
  - ../integration/OPTION_C_INTEGRATION_GUIDE.md (kicli-specific Layer 1 design)
---

# 🖥️ Server Management & Orchestration

This folder addresses **how services are started, stopped, monitored, and coordinated** in kicli-code-assist.

---

## 📌 Current Status

### ✅ What's Recommended (Nov 5, 2026)

Use **stackctl** (Layer 2: Full-stack orchestration):
- All services managed via `stack.yaml`
- Service dependencies declared explicitly
- Health checks, startup ordering automatic
- Multi-target support (local, minikube, k8s)
- No separate "server management" system needed

**Reference:** [`~/dev_doc/SERVICE_ORCHESTRATION_PATTERN.md`](../../../dev_doc/SERVICE_ORCHESTRATION_PATTERN.md)

### ⏳ Design (Not Yet Implemented)

Optional Layer 1 (Single-service supervision for dev):
- `kicli-assist server start --service backend`
- Manual control, live-reload (future)
- Only for development, independent of stackctl

**Reference:** [`OPTION_C_INTEGRATION_GUIDE.md`](../integration/OPTION_C_INTEGRATION_GUIDE.md)

### 📚 Historical (Oct 28 Design, Not Implemented)

Unified Server Management System design:
- Abstract registry-based process control
- Original goal: Multi-project server management
- Status: Superseded by stackctl approach
- Why: stackctl is simpler, proven in ki-knowledge

**Reference:** [`~/dev_doc/server-mngm/`](../../../dev_doc/server-mngm/) (read-only, historical)

---

## 🎯 Next Steps

### For MVP (Get stackctl Working)

1. ✅ Review `~/dev_doc/SERVICE_ORCHESTRATION_PATTERN.md`
2. Write `stack.yaml` with services
3. Test: `stackctl start` / `stackctl logs -f`
4. Integrate into development workflow

### For Layer 1 (Optional, if Needed Later)

1. Review `OPTION_C_INTEGRATION_GUIDE.md` (Layer 1 design)
2. Decide: Is manual single-service control needed?
3. If yes: Implement CLI commands + ki.yaml support
4. If no: Skip; stackctl is sufficient

### To Understand the Architecture

1. Start: `~/dev_doc/SERVICE_ORCHESTRATION_PATTERN.md` (executive summary)
2. Deep dive: `~/dev_doc/server-mngm/SERVER_MANAGEMENT_DESIGN.md` (if curious about historical design)
3. Project-specific: `OPTION_C_INTEGRATION_GUIDE.md` (for kicli decisions)

---

## 📋 File Reference

| Document | Purpose | Status |
|----------|---------|--------|
| `OPTION_C_INTEGRATION_GUIDE.md` | Layer 1 + Layer 2 design for kicli | **Active** (design phase) |
| `~/dev_doc/SERVICE_ORCHESTRATION_PATTERN.md` | Current approach (stackctl-based) | **Active** (recommended) |
| `~/dev_doc/server-mngm/` | Historical design (Oct 28) | **Historical** (reference only) |

---

## ❓ FAQ

**Q: Do I need to implement server_management for kicli-code-assist?**

A: No for MVP. Start with stackctl (Layer 2). Layer 1 is optional for dev ergonomics; many projects (like ki-knowledge) don't need it.

**Q: Where's the Layer 1 CLI design?**

A: See `OPTION_C_INTEGRATION_GUIDE.md` in the integration folder. It's designed but not implemented.

**Q: What's in ~/dev_doc/server-mngm/?**

A: Historical design docs (Oct 28) for a registry-based system. They explain the original thinking but stackctl is now the recommended approach.

**Q: How do I deploy to staging/production?**

A: Use stackctl with K8s target: `stackctl -t k8s start`. See `SERVICE_ORCHESTRATION_PATTERN.md`.

---

**Last Updated**: 2026-11-05  
**Status**: ✅ Active  
**Audience**: DevOps, deployment architects, kicli-code-assist team