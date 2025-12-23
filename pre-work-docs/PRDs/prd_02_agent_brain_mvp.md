
# PRD 02 — Agent Brain (MVP)

## Overview
The Agent Brain provides controlled visibility into what an AI agent knows and allows authorized users to remove knowledge from active use. This PRD defines the MVP functionality required to establish trust, governance, and auditability over agent knowledge.

This PRD intentionally supports **read + soft-forget only** to avoid irreversible actions in MVP.

---

## Goal
Enable Org Admins to:
- Inspect what knowledge an agent uses
- Understand where that knowledge came from
- Disable specific knowledge items so they are no longer used

---

## In Scope (MVP)

### Agent Brain Access
- Each agent has a dedicated “Agent Brain” view
- Accessible only to Org Admins and Knowledge Admins

---

### Knowledge Sources
The Agent Brain must list all **Sources** that contribute to an agent’s knowledge:

Source types:
- Uploaded documents
- Onboarding interview transcripts
- Meeting transcripts

Each source displays:
- Source type
- Title / filename
- Date added
- Added by (user or system)
- Source status (Active / Disabled)

---

### Knowledge Items
From each source, the system extracts **Knowledge Items**.

Each Knowledge Item includes:
- Text content
- Source reference
- Date extracted
- Extraction confidence score
- Status (Active / Disabled)

Knowledge Items are the atomic units used during retrieval.

---

### Soft Forget (Disable Knowledge)
Admins can:
- Disable a Knowledge Item
- Disable an entire Source

Behavior:
- Disabled items are immediately excluded from retrieval
- Disabled items remain stored for audit purposes
- Disabling a source disables all its knowledge items

---

### Agent Usage Enforcement
- Retrieval pipelines must exclude Disabled knowledge
- Agents must not cite Disabled knowledge in responses
- Disabled knowledge must not appear in “used sources” traces

---

## Out of Scope (Explicit)

- Hard deletion
- Editing or rewriting knowledge text
- Granular redaction inside a knowledge item
- Auto-learning from meetings
- Per-user knowledge overrides

---

## User Stories

1. As an Org Admin, I can see all sources contributing to an agent’s knowledge.
2. As an Org Admin, I can inspect individual knowledge items.
3. As an Org Admin, I can disable a knowledge item immediately.
4. As an Org Admin, I can disable an entire source.
5. As an Admin, I can audit who disabled what and when.

---

## Functional Requirements

### View Agent Brain
- Agent Brain page lists sources sorted by date added
- Selecting a source reveals associated knowledge items

### Disable Knowledge Item
- Only Admins and Knowledge Admins can disable
- Action requires confirmation
- Status changes to Disabled immediately

### Disable Source
- Disabling a source disables all child knowledge items
- Re-enabling a source restores all items

### Audit Logging
Each disable/enable action must log:
- Actor
- Timestamp
- Agent ID
- Knowledge Item ID or Source ID
- Action type

---

## Non-Functional Requirements

- All changes must be reversible
- No data loss in MVP
- Deterministic retrieval behavior
- Source traceability preserved

---

## Acceptance Criteria

- Disabled knowledge is never retrieved by agents
- Disabled knowledge is never cited
- Audit log records all actions
- UI reflects status changes immediately

---

## Dependencies

- Agent Service
- Knowledge Service
- RBAC enforcement
- Retrieval pipeline integration

---

## Open Questions

- Should Members be able to request disables?
- Should confidence score be visible in MVP?

---

## Success Metrics

- Time to disable knowledge < 30 seconds
- Zero agent responses citing disabled knowledge
- Admin confidence in agent governance
