# BRIEFING — 2026-07-03T14:45:00+03:00

## Mission
Assess the JobHunt Pro optimization and modernization tasks, decompose into milestones, and orchestrate the Explorer-Worker-Reviewer cycle to implement and verify all requirements.

## 🔒 My Identity
- Archetype: orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_v3
- Original parent: main agent
- Original parent conversation ID: c711605a-6722-44e8-be78-335b9396b681

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_v3\PROJECT.md
1. **Decompose**: Decompose the task into milestones spanning code quality, UI overhaul, test coverage, performance, security, and cleanup, plus the second track (AI, frontend dashboard, stealth scraping, JWT auth, and deployment E2E).
2. **Dispatch & Execute** (pick ONE):
   - **Delegate (sub-orchestrator)**: For large milestones, spawn sub-orchestrators to run the Explorer → Worker → Reviewer cycle.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed at 16 spawns. Kill all timers, write soft handoff, and spawn a successor using `self` archetype.
- **Work items**:
  - Initial assessment [in-progress]
- **Current phase**: 1
- **Current focus**: Decompose and plan milestones

## 🔒 Key Constraints
- NEVER write, modify, or create source code files directly.
- NEVER run build/test commands yourself — require workers to do so.
- May use file-editing tools only for metadata/state files (.md) in your .agents/ folder.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Zero-tolerance for integrity violations: no hardcoding, no dummy/facade implementations, no circumventing checks.
- Audit is a binary veto. If the auditor reports INTEGRITY VIOLATION, rollback the milestone.

## Current Parent
- Conversation ID: c711605a-6722-44e8-be78-335b9396b681
- Updated: 2026-07-03T14:45:00+03:00

## Key Decisions Made
- Confirmed the existence of both Flask backend (core/web/templates) and FastAPI/Next.js/scrapers codebases.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| explorer_m1 | teamwork_preview_explorer | Run existing test suites, evaluate all files, identify bug details and security issues | completed | c3145e36-f27a-4e22-8e6e-f819549712d3 |
| worker_fix_imports | teamwork_preview_worker | Fix database shim imports and run initial tests / next builds | completed | 8c59c172-ff97-4a59-97f6-f23f36c831c4 |
| explorer_test_failures | teamwork_preview_explorer | Audit test failures in pytest suites | completed | 35299987-33e1-4073-a05b-cbd20cc81edc |
| worker_m2_e2e | teamwork_preview_worker | Fix FastAPI and Next.js stack E2E issues | completed | 68273ac7-fd8e-470f-a58b-0f4ffe9f16fc |
| auditor_m2 | teamwork_preview_auditor | Perform forensic integrity audit on Milestone 2 changes | completed | adf167f8-05d6-402a-9a30-2a66e1e77c0a |
| worker_m3_flask | teamwork_preview_worker | Fix Flask stack quality and security issues | in-progress | b26e0bb4-6e46-4487-95e6-3ff3c1f3c12b |

## Succession Status
- Succession required: no
- Spawn count: 6 / 16
- Pending subagents: [b26e0bb4-6e46-4487-95e6-3ff3c1f3c12b]
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: c816011a-6036-43b6-8dfe-f2cc78b415ce/task-21
- Safety timer: none

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_v3\ORIGINAL_REQUEST.md — Original user request containing requirements and acceptance criteria
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_v3\BRIEFING.md — Persistent memory index for the orchestrator
