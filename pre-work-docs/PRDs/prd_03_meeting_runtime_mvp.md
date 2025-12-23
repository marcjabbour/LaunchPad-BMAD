
# PRD 03 — Meeting Runtime (MVP)

## Overview
The Meeting Runtime enables AI agents to be deployed into live meetings, listen to conversation streams, make controlled decisions about participation, generate artifacts, and persist outputs. This PRD defines the MVP behavior of the live agent execution system.

The Meeting Runtime is the core value loop of LaunchPad.

---

## Goal
Enable a single AI agent to:
- Join a live meeting
- Listen continuously
- Decide when to act
- Generate artifacts on demand
- Persist outputs reliably

All behavior must be controlled, auditable, and resumable.

---

## In Scope (MVP)

### Supported Meeting Platforms
- One platform only (initial adapter)
- Platform-agnostic internal interface

---

### Agent Deployment
- Admins can deploy an Active agent into a meeting
- Deployment creates a unique Agent Session
- An agent may have only one active session per meeting

---

### Session Lifecycle

| State | Description |
|------|-------------|
| Initializing | Agent is joining |
| Listening | Agent is ingesting transcript |
| Acting | Agent is responding or generating |
| Paused | Waiting on approval |
| Completed | Meeting ended |
| Failed | Runtime error |

---

### Transcript Ingestion
- Meeting audio is transcribed continuously
- Transcript chunks are streamed to runtime
- Each chunk includes speaker, timestamp, and text

---

### Decision Loop
For each transcript chunk, the agent must:
1. Classify relevance
2. Decide whether to act
3. Select allowed tools
4. Produce output or remain silent

---

### Speaking Rules
The agent respects configured speaking style:
- Silent unless asked
- Reactive
- Proactive with approval

Agent must not interrupt human speakers.

---

### Side-Channel Messaging
- Internal users can message the agent privately
- Messages influence agent behavior
- Side-channel messages are logged

---

### Artifact Generation
Agent may generate:
- Text summaries
- Action items
- Diagrams

Artifacts must:
- Be linked to the meeting
- Be linked to the agent session
- Be persisted immediately

---

### Human Approval Gates
Actions requiring approval:
- Speaking proactively
- Generating external-facing artifacts

Agent enters Paused state until resolved.

---

## Out of Scope (Explicit)

- Multi-agent orchestration
- Auto-inviting agents
- Voice customization
- Screen sharing
- Autonomy escalation
- Multi-meeting concurrency

---

## User Stories

1. As an Admin, I can deploy an agent to a meeting.
2. As a User, I can privately message the agent.
3. As an Agent, I can decide to remain silent.
4. As a User, I can approve or reject agent actions.
5. As a User, I can see artifacts created during a meeting.

---

## Functional Requirements

### Deploy Agent
- Agent must be Active
- Meeting ID must be valid
- Agent session is created

### Resume on Failure
- Session state must be persisted
- Agent can resume listening after restart

### Tool Enforcement
- Only permitted tools may be invoked
- Disallowed tools must error safely

---

## Non-Functional Requirements

- Low-latency transcript handling
- Deterministic state transitions
- Full audit logging
- Idempotent artifact creation

---

## Acceptance Criteria

- Agent joins meeting successfully
- Agent remains silent unless allowed
- Artifacts are persisted and visible
- Disabled tools are never invoked
- Session recovers from restart

---

## Dependencies

- Agent Service
- Knowledge Service
- Artifact Service
- LangGraph runtime
- Meeting platform adapter

---

## Open Questions

- Should users see real-time agent state?
- Should approval timeout auto-resolve?

---

## Success Metrics

- Agent joins meeting < 10 seconds
- Zero unapproved agent speech
- Zero lost artifacts
