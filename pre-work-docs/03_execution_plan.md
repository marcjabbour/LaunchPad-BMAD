
# LaunchPad — Execution Plan

## Guiding Principle
Ship the smallest system that proves agents can create persistent value inside meetings.

---

## MVP Definition

### Goals
- Agent joins a live meeting
- Produces useful artifacts
- Everything is persisted and reviewable

### Scope
- One meeting platform
- One agent role
- Agent Studio (basic)
- Read-only Agent Brain
- Artifact persistence
- Admin/Member RBAC

### Explicit Non-Goals
- Full autonomy
- Multi-platform meetings
- Hard deletes
- Agent marketplaces

---

## Build Order

1. Auth & Org setup
2. Agent Studio (create/configure)
3. Knowledge ingestion (docs + transcripts)
4. Meeting Runtime (LangGraph)
5. Artifact persistence
6. Admin review UI

---

## V1 Expansion

- Knowledge editing and redaction
- Approval queues
- Agent templates
- Multi-agent collaboration
- Project-level scopes

---

## V2 Expansion

- Multi-platform adapters
- Advanced policy engine
- Compliance and exports
- Agent marketplace
- A2A protocol support

---

## Risks

- Over-automation too early
- Unclear governance boundaries
- Meeting platform instability

---

## Mitigations

- Human approval first
- Clear MVP scope
- Adapter-based integrations
