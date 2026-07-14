# BRIEFING — 2026-07-12T23:50:00+03:00

## Mission
Implement Milestone 2 items (IMP-034, IMP-039, IMP-183, IMP-247) using the Project Orchestrator procedure.

## 🔒 My Identity
- Archetype: sub_orch
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m2
- Original parent: parent
- Original parent conversation ID: ecf3f52e-0c8a-4765-84a1-4ec7100e1f07

## 🔒 My Workflow
- **Pattern**: Project (Sub-orchestrator)
- **Scope document**: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m2\SCOPE.md
1. **Decompose**: Assess complexity and either delegate to sub-orchestrators or execute the Explorer -> Worker -> Reviewer -> Challenger -> Forensic Auditor -> Gate loop.
2. **Dispatch & Execute**:
   - **Direct (iteration loop)**: Spawn Explorer(s) -> Worker -> Reviewer(s) -> Challenger(s) -> Forensic Auditor -> Gate.
3. **On failure**:
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (last resort)
4. **Succession**: Self-succeed at 16 spawns. Write handoff.md, spawn successor, exit.
- **Work items**:
  1. IMP-034: N+1 query elimination audit [pending]
  2. IMP-039: Celery task group/chord for bulk email [pending]
  3. IMP-183: Arabic NLP job matching [pending]
  4. IMP-247: CV PDF parsing accuracy [pending]
- **Current phase**: 1
- **Current focus**: Assess complexity and locate codebase structure.

## 🔒 Key Constraints
- NEVER write, modify, or create source code files directly.
- NEVER run build/test commands yourself — require workers to do so.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Hard veto on forensic audit failure.

## Current Parent
- Conversation ID: ecf3f52e-0c8a-4765-84a1-4ec7100e1f07
- Updated: not yet

## Key Decisions Made
- None yet.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| explorer_1 | teamwork_preview_explorer | Explore codebase for M2 | pending | 55623688-fbda-46dd-aba0-e82415279c07 |
| explorer_2 | teamwork_preview_explorer | Explore codebase for M2 | pending | 6ae3941c-8d9b-4eba-a6a5-28f8f4ad662b |
| explorer_3 | teamwork_preview_explorer | Explore codebase for M2 | pending | 4ce12f74-59ce-4bfc-9caf-c3f61a5a74ef |

## Succession Status
- Succession required: no
- Spawn count: 3 / 16
- Pending subagents: 55623688-fbda-46dd-aba0-e82415279c07, 6ae3941c-8d9b-4eba-a6a5-28f8f4ad662b, 4ce12f74-59ce-4bfc-9caf-c3f61a5a74ef
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: 3e49a746-5cea-4b7e-9423-69f0eab49048/task-17
- Safety timer: none

## Artifact Index
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m2\SCOPE.md — Milestone Scope Document
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m2\ORIGINAL_REQUEST.md — Original User Request
