## 2026-07-12T09:00:46Z

You are tasked with implementing Milestone 1: Deploy Frontend to Cloudflare Pages.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please execute the following steps:
1. Edit `frontend/next.config.ts` to enable static HTML export:
   - Uncomment `output: "export"`
   - Set `unoptimized: true` under `images`
2. Create `frontend/public/_worker.js` containing the Cloudflare Pages Function proxy script. Set its default fallback backend URL to `https://jhfguf.pythonanywhere.com`. The script must support WebSocket handshakes, route proxy paths (`/api/`, `/ws/`, `/_/pa/`, `/scrape`, `/health`) and forward headers correctly.
3. Edit `web/app_v2.py` around line 842 to update `allow_origin_regex` to:
   `allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|chrome-extension://.*|https?://.*\.pages\.dev|https?://.*\.koyeb\.app"`
4. Run `npm run build` in the `frontend` directory to verify that Next.js builds successfully in static export mode and outputs files in `frontend/out/`.
5. Run the backend tests using `pytest` to ensure that no regressions are introduced and that the test suite passes cleanly.
6. Write a complete handoff report to `handoff.md` in your working directory `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m1_cloudflare_pages`. Show the command output from the build and test stages.
