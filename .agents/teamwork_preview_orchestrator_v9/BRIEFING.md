# BRIEFING — 2026-07-06T12:20:00+03:00

## Mission
Audit and enhance every full-page HTML template in web/templates/ and web/templates/en/ for content and UI quality, premium glassmorphism style, navigation integrity, backend route completeness, performance/SEO, and ensure 253 tests pass.

## 🔒 My Identity
- Archetype: orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_orchestrator_v9
- Original parent: main agent
- Original parent conversation ID: 0d067221-7d91-440e-bb1e-cb29ceac3991

## 🔒 My Workflow
- **Pattern**: Project Pattern
- **Scope document**: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_orchestrator_v9\PROJECT.md
1. **Decompose**: Decompose the task into milestones corresponding to requirements R1 to R6.
2. **Dispatch & Execute**:
   - **Delegate**: Use explorer, worker, reviewer, challenger, and auditor subagents to execute and verify the changes.
3. **On failure**:
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed at 16 spawns, write handoff.md, spawn successor.
- **Work items**:
  - M1: Planning and Setup [done]
  - M2: R1 Deep Per-Page Content Audit & Enhancement [pending]
  - M3: R2 Premium UI Polish [pending]
  - M4: R3 Navigation & User Flow Integrity [pending]
  - M5: R4 Backend Route & Feature Completeness [pending]
  - M6: R5 Performance & SEO Final Polish [pending]
  - M7: R6 Test Suite Verification & Victory [pending]
- **Current phase**: 1
- **Current focus**: Planning and Setup

## 🔒 Key Constraints
- CSS Logical Properties must be used instead of physical ones (no margin-left/padding-right/left/right/etc.).
- Arabic typography: Cairo/Tajawal fonts, minimum 16px, line-height 1.6 to 2.0, no letter-spacing.
- Form inputs must have dir="auto".
- Every full page must use dark gradient backgrounds and premium glassmorphism card style.
- All buttons must have hover:transform and hover:box-shadow.
- Run python qa_audit_r4.py to check CSS compliance.
- Run python qa_spider.py to check for 404 links.
- Make sure to test page loading and check _pa_server.log for any Jinja2 UndefinedErrors.
- Ensure the full test suite passes with python -m pytest tests/ -q (253 passed, 0 failed).
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.

## Current Parent
- Conversation ID: 0d067221-7d91-440e-bb1e-cb29ceac3991
- Updated: not yet

## Key Decisions Made
- Decompose the project into sequential milestones mapping to the requirements R1-R6.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| explorer_1 | teamwork_preview_explorer | Arabic template content and UI audit | completed | 68efc0db-fe24-4a33-ac1c-039cf590eb98 |
| explorer_2 | teamwork_preview_explorer | English template content and UI audit | completed | d0ed9cbd-ab2a-4c05-b979-23caa54f1bcb |
| explorer_3 | teamwork_preview_explorer | Backend route and SEO/perf audit | completed | 14cd1371-c1ea-47c7-baca-67592f535f14 |
| worker_1 | teamwork_preview_worker | Code and template enhancement worker | completed | 7b91fe10-7629-4e64-8d6e-795bb6e7fc65 |
| reviewer_1 | teamwork_preview_reviewer | First independent code reviewer | pending | 6eb7b6f1-9c5b-40b0-bd26-a420609747a4 |
| reviewer_2 | teamwork_preview_reviewer | Second independent code reviewer | pending | b04fa117-7e1d-421a-a785-998dcea33f9f |
| challenger_1 | teamwork_preview_challenger | First empirical challenger and verifier | pending | 54dd8eb7-deed-42c9-852b-340130623bce |
| challenger_2 | teamwork_preview_challenger | Second empirical challenger and verifier | pending | f0b01336-0101-4b0e-9aef-4c536959d3ee |

## Succession Status
- Succession required: no
- Spawn count: 8 / 16
- Pending subagents: 6eb7b6f1-9c5b-40b0-bd26-a420609747a4, b04fa117-7e1d-421a-a785-998dcea33f9f, 54dd8eb7-deed-42c9-852b-340130623bce, f0b01336-0101-4b0e-9aef-4c536959d3ee
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: task-21
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run manage_task(Action="list") — re-create if missing

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_orchestrator_v9\plan.md — Project plan
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_orchestrator_v9\progress.md — Progress tracking
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\PROJECT.md — Global project scope
