
# PRD 05 — RBAC & Permissions (MVP)

## Overview
Role-Based Access Control (RBAC) defines who can see, create, modify, deploy, and govern resources in LaunchPad. This PRD specifies the minimal, non-ambiguous permission model required to safely support multi-user organizations in the MVP.

RBAC is foundational to trust, governance, and enterprise readiness.

---

## Goal
Ensure that:
- Users only see what they are permitted to see
- Only authorized users can modify agents, knowledge, or artifacts
- All sensitive actions are auditable
- Permission logic is deterministic and enforceable across services

---

## Core Concepts

### Organization
- Top-level tenant boundary
- All users, agents, meetings, and artifacts belong to exactly one Org

### Project
- Optional sub-scope within an Org
- Used for grouping meetings, agents, and artifacts

### Resource Types
RBAC applies to:
- Agents
- Agent Versions
- Knowledge Sources
- Knowledge Items
- Meetings
- Agent Sessions
- Artifacts
- Audit Logs

---

## Roles (MVP)

### Org Admin
Full control over the organization.

Permissions:
- Manage users and roles
- Create, edit, activate, disable agents
- View and modify Agent Brain (PRD 02)
- Deploy agents into meetings
- Approve agent actions
- View all artifacts
- Modify artifact visibility
- View audit logs

---

### Knowledge Admin
Specialized governance role.

Permissions:
- View Agent Brain
- Disable/enable knowledge sources and items
- View audit logs related to knowledge
- Cannot create or deploy agents
- Cannot manage users

---

### Member
Standard user.

Permissions:
- View agents
- Deploy agents into meetings (if allowed by Admin)
- View artifacts they have access to
- Message agents via side-channel
- Approve agent actions (if delegated)

Cannot:
- Edit agents
- Modify knowledge
- View audit logs

---

### Viewer
Read-only role.

Permissions:
- View artifacts they have access to
- View meetings they were part of

Cannot:
- Deploy agents
- Modify anything

---

## Role Assignment

- Only Org Admins can assign roles
- Users may have exactly one role per Org
- Role changes take effect immediately

---

## Permission Enforcement

### Enforcement Points
RBAC must be enforced at:
- API layer
- Service layer
- UI layer

No client-side-only enforcement is allowed.

---

### Default Permissions Matrix (MVP)

| Action | Admin | Knowledge Admin | Member | Viewer |
|------|------|----------------|--------|--------|
| Create Agent | ✅ | ❌ | ❌ | ❌ |
| Edit Agent | ✅ | ❌ | ❌ | ❌ |
| Activate/Disable Agent | ✅ | ❌ | ❌ | ❌ |
| View Agent Brain | ✅ | ✅ | ❌ | ❌ |
| Disable Knowledge | ✅ | ✅ | ❌ | ❌ |
| Deploy Agent | ✅ | ❌ | ✅* | ❌ |
| View Artifacts | ✅ | ✅ | ✅ | ✅ |
| Change Artifact Visibility | ✅ | ❌ | ❌ | ❌ |
| View Audit Logs | ✅ | ✅* | ❌ | ❌ |

*subject to admin configuration

---

## Artifact Visibility Interaction

RBAC combines with artifact visibility rules:

Access granted if:
- User role permits viewing artifacts
- AND artifact visibility scope allows access
- AND user belongs to the relevant Org/Project

---

## Audit Logging

The following actions must be logged:
- Role assignment changes
- Agent creation, activation, disabling
- Knowledge disable/enable
- Artifact visibility changes
- Agent deployments

Audit logs must include:
- Actor
- Timestamp
- Action type
- Resource ID
- Outcome

---

## Out of Scope (Explicit)

- Custom roles
- Attribute-based access control (ABAC)
- Temporary or time-bound roles
- Cross-org access
- External identity providers

---

## Non-Functional Requirements

- Permission checks must be deterministic
- Authorization latency < 50ms
- No silent permission failures
- Centralized policy logic

---

## Acceptance Criteria

- Unauthorized actions are rejected consistently
- Role changes take effect immediately
- Audit logs reflect all privileged actions
- No cross-org data leakage

---

## Dependencies

- Auth system
- User management
- Agent Service
- Knowledge Service
- Artifact Service

---

## Open Questions

- Should Members be allowed to deploy agents by default?
- Should Knowledge Admins view all audit logs or only knowledge-related?

---

## Success Metrics

- Zero permission-related security incidents
- Admin confidence in access control
- No ambiguous permission behavior
