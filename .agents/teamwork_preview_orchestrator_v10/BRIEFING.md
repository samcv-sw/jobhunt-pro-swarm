# BRIEFING — 2026-07-06T13:14:44+03:00

## Mission
Coordinate the team to audit and fix the 18 live pages of JobHunt Pro and ensure zero regression.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_orchestrator_v10
- Original parent: top-level
- Original parent conversation ID: fd084c63-798d-4f5d-ba06-5958cda1ed38

## 🔒 My Workflow
- Pattern: Project
- Scope document: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_orchestrator_v10\PROJECT.md
1. **Decompose**: Decompose the task into milestones:
   - Milestone 1: Live Page Audit
   - Milestone 2: Fix Non-Functional Buttons
   - Milestone 3: Fix Content Issues
   - Milestone 4: Fix Navigation Consistency
   - Milestone 5: Verify via E2E and Unit Tests
2. **Dispatch & Execute** (pick ONE):
   - **Delegate (sub-orchestrator)**: When an item is too large, spawn a sub-orchestrator for it.
   - **Direct (iteration loop)**: Explorer -> Worker -> Reviewer -> Challenger -> Auditor.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: at 16 spawns, write handoff.md, spawn successor.
- **Work items**:
  1. Live Page Audit [pending]
  2. Implement Fixes for Buttons & Content [pending]
  3. Navigation & Consistency fixes [pending]
  4. Test Suite and Regression Checks [pending]
- **Current phase**: 1
- **Current focus**: Milestone 1: Live Page Audit

## 🔒 Key Constraints
- Never write, modify, or create source code files directly.
- Never run build/test commands yourself — require workers to do so.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.

## Current Parent
- Conversation ID: fd084c63-798d-4f5d-ba06-5958cda1ed38
- Updated: 2026-07-06T13:14:44+03:00

## Key Decisions Made
- Initializing project pattern.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| explorer_m1_1 | teamwork_preview_explorer | Audit pages 1-6 | pending | 496e9711-697a-4015-b3ab-4f0f49a809f6 |
| explorer_m1_2 | teamwork_preview_explorer | Audit pages 7-12 | pending | b33ac7a9-109a-466b-a9b8-4ce973b996e4 |
| explorer_m1_3 | teamwork_preview_explorer | Audit pages 13-18 | pending | aedd0d12-4805-4105-a094-0430e7510873 |

## Succession Status
- Succession required: no
- Spawn count: 3 / 16
- Pending subagents: 496e9711-697a-4015-b3ab-4f0f49a809f6, b33ac7a9-109a-466b-a9b8-4ce973b996e4, aedd0d12-4805-4105-a094-0430e7510873
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: 7a4bf194-0a9b-4a62-9eb6-35e05c0ec597/task-23
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_orchestrator_v10\progress.md — heartbeat progress log
