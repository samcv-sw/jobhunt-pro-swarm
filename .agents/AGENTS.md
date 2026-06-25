# Antigravity Workspace Rules & Instructions

Whenever a new chat session is started in this workspace, the agent MUST automatically perform the following steps on its very first turn:

1. **Read Project State**:
   - Read [ANTIGRAVITY_STATE_SUMMARY.md](file:///C:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi/ANTIGRAVITY_STATE_SUMMARY.md) to understand the current state, active objectives, and the previous conversation ID.
   - Read [AUTO_OPTIMIZATION_LOG.md](file:///C:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi/AUTO_OPTIMIZATION_LOG.md) and [.antigravity_improvements.json](file:///C:/Users/samde/Desktop/📂 Folders & Projects/cv sam new ma3 kimi/.antigravity_improvements.json) to see what optimizations have already been applied.

2. **Sync the Conversation ID**:
   - Run the loop script command: `python scripts/antigravity_loop.py loop` using `run_command`. This dynamically finds the active conversation directory in the Antigravity IDE and updates the state summary report with the new conversation ID.

3. **Verify Workspace Health**:
   - Run the health check command: `python scripts/antigravity_loop.py check` to check database connections, schema validation, and config files.
   - Check `_pa_error.log` or the `logs/` directory for any recent failures or crashes that need auto-healing.

4. **Continuous Optimization Plan**:
   - If the user runs the chat with the `/goal` command or requests optimization:
     - Identify the most high-impact files to optimize (e.g., refactoring code, fixing bugs, cleaning up logs, performance tuning).
     - Implement the changes, run tests with `pytest`, log the improvements with `python scripts/antigravity_loop.py log-improvement --summary "..."`, and update the state report.
     - Repeat this cycle continuously until the estimated token limit (from `ANTIGRAVITY_STATE_SUMMARY.md`) reaches ~85% or 1.7M tokens.
