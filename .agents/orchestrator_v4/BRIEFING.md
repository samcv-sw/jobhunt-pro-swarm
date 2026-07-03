# BRIEFING — 2026-07-03T16:12:34+03:00

## Mission
Expand JobHunt Pro into a globally scalable enterprise platform by implementing Kubernetes deployments, a Vector DB for RAG, a Mobile App, and Stripe Billing.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_v4
- Original parent: main agent
- Original parent conversation ID: c64f98b4-7d41-49c8-a38b-e116514ea5e4

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_v4\PROJECT.md
1. **Decompose**: Decompose the 4 requirements (K8s, Vector DB, Mobile App, Stripe Billing) into parallel/sequential milestones and establish an E2E testing track.
2. **Dispatch & Execute**:
   - **Delegate (sub-orchestrator)**: Spawn a sub-orchestrator or specialized worker for each milestone.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed at 16 spawns, write handoff.md, spawn successor.
- **Work items**:
  1. Initialize Plan & Progress [done]
  2. Implement K8s Deployment [in-progress]
  3. Implement Vector DB/RAG Integration [in-progress]
  4. Implement React Native Mobile App [in-progress]
  5. Implement Stripe Billing [in-progress]
  6. E2E Verification & Audit [pending]
- **Current phase**: 2
- **Current focus**: Implement all features in parallel via sub-orchestrators

## 🔒 Key Constraints
- Must follow AGENTS.md rules (CSS Logical Properties, Arabic typography, form dir attributes for any UI/mobile work).
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Victory Audit is MANDATORY before reporting completion.

## Current Parent
- Conversation ID: c64f98b4-7d41-49c8-a38b-e116514ea5e4
- Updated: 2026-07-03T16:12:34+03:00

## Key Decisions Made
- Decompose task into 4 milestones matching requirements, plus E2E verification.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| sub_orch_k8s | self | Implement K8s Deployment | in-progress | bb20b5b1-9c5c-412c-9da2-4c162a845a3b |
| sub_orch_rag | self | Implement Vector DB/RAG | in-progress | c4e4ddf0-be49-4898-928d-66a9918ca89c |
| sub_orch_mobile | self | Implement Mobile App | in-progress | 8ab2f959-ac0e-4a54-8907-d96a63bf150e |
| sub_orch_billing | self | Implement Stripe Billing | in-progress | 3f260753-c648-4e9a-8d25-1bd7e90b2de0 |

## Succession Status
- Succession required: yes
- Spawn count: 4 / 16
- Pending subagents: bb20b5b1-9c5c-412c-9da2-4c162a845a3b, c4e4ddf0-be49-4898-928d-66a9918ca89c, 8ab2f959-ac0e-4a54-8907-d96a63bf150e, 3f260753-c648-4e9a-8d25-1bd7e90b2de0
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: 03a5d8e5-1b4f-455a-82b0-0c40fed8c7c2/task-21
- Safety timer: 03a5d8e5-1b4f-455a-82b0-0c40fed8c7c2/task-67
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_v4\ORIGINAL_REQUEST.md — Original User Request record
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_v4\PROJECT.md — Global index, architecture, milestones, interfaces
