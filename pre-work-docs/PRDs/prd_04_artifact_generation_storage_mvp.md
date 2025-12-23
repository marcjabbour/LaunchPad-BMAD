
# PRD 04 — Artifact Generation & Storage (MVP)

## Overview
Artifacts are the durable outputs produced by AI agents during meetings. This PRD defines how artifacts are generated, stored, linked, permissioned, and audited in the MVP.

Artifacts are the primary mechanism by which ephemeral meetings become persistent organizational knowledge.

---

## Goal
Enable AI agents to generate artifacts during meetings and ensure those artifacts are:
- Persisted reliably
- Discoverable
- Permissioned
- Auditable
- Linked to their origin (agent + meeting)

---

## In Scope (MVP)

### Supported Artifact Types
The MVP supports the following artifact types:

- Meeting Summary (text)
- Action Items (structured text)
- Diagrams (text-based, e.g. Mermaid)
- Notes / Draft Documents

No binary uploads (PDF, images) in MVP.

---

### Artifact Creation
Artifacts can be created by:
- AI agents during a meeting
- Only through allowed tools (enforced by Agent Studio permissions)

Each artifact must be created in the context of:
- A Meeting
- An Agent Session

---

### Artifact Metadata
Each artifact must store the following metadata:

- Artifact ID
- Artifact Type
- Title
- Content (text)
- Created At
- Created By (Agent ID)
- Agent Session ID
- Meeting ID
- Project (optional)
- Visibility Scope
- Version Number

---

### Versioning
- Artifacts are versioned immutably
- Each update creates a new version
- Previous versions remain accessible (read-only)

---

### Visibility & Permissions
Artifacts support three visibility levels:

| Level | Description |
|------|-------------|
| Private | Visible only to creator and Admins |
| Project | Visible to project members |
| Org | Visible to all org members |

Default visibility:
- Meeting Summary → Org
- Action Items → Project
- Notes → Private

Only Admins can change visibility in MVP.

---

### Artifact Persistence
- Artifacts must be persisted immediately upon creation
- Artifact creation must be idempotent
- No artifact loss is acceptable

---

### Artifact Listing & Viewing
Users can:
- View artifacts by meeting
- View artifacts by agent
- View artifacts by project

Artifacts display:
- Content
- Metadata
- Version history

---

## Out of Scope (Explicit)

- Artifact editing by humans
- Binary files (images, PDFs)
- External sharing
- Search
- Comments
- Deletion

---

## User Stories

1. As a User, I can view artifacts created during a meeting.
2. As an Admin, I can see which agent created an artifact.
3. As a User, I can trust artifacts will not be lost.
4. As an Admin, I can audit artifact history.

---

## Functional Requirements

### Create Artifact
- Must include meeting and agent session IDs
- Must validate tool permissions
- Must persist before acknowledgment

### Version Artifact
- Updating content creates new version
- Version numbers increment monotonically

### Enforce Visibility
- Access checks enforced on read
- Unauthorized access returns error

---

## Non-Functional Requirements

- Strong consistency on writes
- Idempotent creation
- Low-latency reads
- Full audit logging

---

## Acceptance Criteria

- Artifacts persist immediately after generation
- Artifacts are visible according to permissions
- Version history is preserved
- No duplicate artifacts on retry

---

## Dependencies

- Meeting Runtime
- Agent Studio (tool permissions)
- Auth & RBAC
- Storage layer

---

## Open Questions

- Should Admins edit artifact visibility post-creation?
- Should drafts auto-promote to summaries?

---

## Success Metrics

- Zero lost artifacts
- Artifact availability < 1s after creation
- Admin confidence in artifact traceability
