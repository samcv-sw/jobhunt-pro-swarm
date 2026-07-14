# BRIEFING — 2026-07-12T11:56:36+03:00

## Mission
Orchestrate the implementation of cloud optimizations, performance upgrades, and reliability enhancements (R1-R5) for JobHunt Pro.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_cloud_optimize_gen4
- Original parent: parent
- Original parent conversation ID: 447c3988-bae9-40f3-90d0-718fa7c874a5

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_cloud_optimize_gen4\plan.md
1. **Decompose**: Decompose requirements (R1-R5) into 5 milestones, specifying interface contracts and verification criteria.
2. **Dispatch & Execute**:
   - **Direct (iteration loop)**: For each milestone, run the loop: Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: at 16 spawns, write handoff.md, spawn successor
- **Work items**:
  1. R1. Deploy Frontend to Cloudflare Pages [pending]
  2. R2. Platform-Specific Intelligent Scraper Rate Limit Profiles [pending]
  3. R3. Database Optimization & Bulk Inserts [pending]
  4. R4. SSRF Prevention & Scraper URL Validation [pending]
  5. R5. Persistent logging to Logtail [pending]
- **Current phase**: 1
- **Current focus**: Decomposing requirements and planning milestones

## 🔒 Key Constraints
- NEVER write, modify, or create source code files directly.
- NEVER run build/test commands yourself — require workers to do so.
- You MAY use file-editing tools ONLY for metadata/state files (.md) in your .agents/ folder.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh

## Current Parent
- Conversation ID: 447c3988-bae9-40f3-90d0-718fa7c874a5
- Updated: not yet

## Key Decisions Made
- Started orchestration for 2026-07-12 Cloud Optimizations.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| m1_exp_nextjs | teamwork_preview_explorer | M1 NextJS static export exploration | completed | c7156586-7f09-42e5-a0a9-73fccc5e7e8c |
| m1_exp_vue | teamwork_preview_explorer | M1 Vue static export exploration | completed | dcfd9590-63ee-4e55-b8c2-9f4180caa415 |
| m1_exp_routing | teamwork_preview_explorer | M1 Cloudflare routing exploration | completed | 636b7b71-940e-4859-80a5-041fbe02da69 |
| m1_worker | teamwork_preview_worker | M1 Cloudflare Pages implementation | in-progress | ef2e743b-7731-4ba9-8814-40aebcea0d15 |

## Succession Status
- Succession required: no
- Spawn count: 4 / 16
- Pending subagents: ef2e743b-7731-4ba9-8814-40aebcea0d15
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: not started
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_cloud_optimize_gen4\plan.md — Milestone plan and contracts
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\orchestrator_cloud_optimize_gen4\progress.md — Progress heartbeat log
