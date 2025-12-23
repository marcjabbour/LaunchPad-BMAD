
# PRD 01 — Agent Studio (MVP)

## Overview
The Agent Studio is the foundational surface in LaunchPad where organization administrators create, configure, version, and manage AI agents. This PRD defines the MVP scope required to support agent creation and readiness for deployment into meetings.

This PRD is intentionally strict to prevent overbuilding and ambiguity.

---

## Goal
Enable an Org Admin to create a role-based AI agent that is:
- Configurable
- Versioned
- Governed
- Deployable into meetings

---

## In Scope (MVP)

### Agent Creation
Admins can create an agent with the following required fields:

- Agent Name (string, unique per org)
- Role (PM, Designer, Engineer, Custom)
- Description (free text)
- Personality Profile (enum)
- Speaking Style (enum)
- Tool Permissions (checkbox list)
- Knowledge Scope (Org / Project)
- Status (Draft / Active / Disabled)

---

### Agent Configuration

Admins can configure:

#### Personality Profile
- Concise
- Neutral
- Proactive
- Reserved

#### Speaking Style
- Silent unless asked
- Reactive
- Proactive with approval

#### Tool Permissions
- Generate text documents
- Generate diagrams
- Generate images
- Summarize meetings

Tool permissions are enforced at runtime.

---

### Agent Versioning
- Every save creates a new immutable Agent Version
- Only one version can be Active at a time
- Disabled agents cannot be deployed

---

### Agent Lifecycle States

| State | Description |
|-----|------------|
| Draft | Editable, not deployable |
| Active | Deployable |
| Disabled | Not deployable |

---

### Agent Listing
Admins and Members can:
- View list of agents
- See role, status, last updated
- Filter by status and role

Only Admins can edit.

---

## Out of Scope (Explicit)

- Knowledge ingestion
- Knowledge editing
- Agent memory inspection
- Agent cloning/templates
- Per-meeting overrides
- Voice selection
- Autonomy tuning

---

## User Stories

1. As an Org Admin, I can create a new agent so it can later be onboarded.
2. As an Org Admin, I can configure an agent’s behavior and tools.
3. As an Org Admin, I can disable an agent to prevent deployment.
4. As a Member, I can view available agents.
5. As an Admin, I can ensure only Active agents are deployable.

---

## Functional Requirements

### Create Agent
- Agent name must be unique per org
- Required fields must be validated
- New agent starts in Draft state

### Edit Agent
- Editing creates a new version
- Previous versions are immutable
- Version history is viewable (read-only)

### Activate Agent
- Only Admins can activate
- Agent must have all required fields set

### Disable Agent
- Disabled agents cannot be deployed
- Existing sessions are unaffected

---

## Non-Functional Requirements

- All changes are auditable
- Version history must be preserved
- API-first design
- Deterministic behavior

---

## Acceptance Criteria

- Admin can create agent with required fields
- Agent remains Draft until activated
- Active agent appears as deployable
- Disabled agent cannot be selected for meetings
- Version history is preserved and visible

---

## Dependencies

- Org & Auth system
- RBAC enforcement
- Agent persistence layer

---

## Open Questions

- Do Members see version history?
- Are Custom roles unrestricted in MVP?

---

## Success Metrics

- Time to create agent < 2 minutes
- Zero runtime deployments of Draft/Disabled agents
