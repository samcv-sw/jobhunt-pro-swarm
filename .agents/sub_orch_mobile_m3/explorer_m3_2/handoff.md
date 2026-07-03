# Handoff Report — Explorer 2 (Milestone 3)

This handoff report summarizes the findings, reasoning, and implementation plans for the React Native Expo Mobile App (Milestone 1).

## 1. Observation
We examined the workspace and located the following configuration files and backend routes:

*   **Workspace structure**: The top-level directory contains a `web/` folder but currently lacks a `mobile/` directory, confirming that initialization from scratch is required.
*   **Backend Endpoints in `web/frontend_api.py`**:
    *   **User Lookup by Email** (Line 198-199):
        ```python
        @router.get("/api/user/by-email")
        async def user_by_email(email: str):
        ```
    *   **User Stats** (Line 242-243):
        ```python
        @router.get("/api/user/stats")
        async def user_stats(user_id: str = ""):
        ```
    *   **Campaign Creation** (Line 385-386):
        ```python
        @router.post("/api/campaign/create")
        async def campaign_create(request: Request):
        ```
    *   **Campaign List** (Line 431-432):
        ```python
        @router.get("/api/campaign/list")
        async def campaign_list(user_id: str = ""):
        ```
    *   **User Jobs List** (Line 481-482):
        ```python
        @router.get("/api/jobs/user")
        async def jobs_user(user_id: str = "", limit: int = 20):
        ```
*   **Backend Endpoints in `web/routers/dashboard.py`**:
    *   This router relies on browser session authentication (e.g. `request.session.get("user_id")` at lines 50, 95, 119). This is unsuitable for stateless mobile client calls, confirming we must target the `web/frontend_api.py` endpoints which accept query/body parameter credentials.
*   **AGENTS.md Directives**:
    *   Injected user rules require strict Arabic typography rules (`'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif`, min font size `14px` / recommended `16px`, line-height `1.6`-`2.0`, no `letter-spacing`), logical styles (e.g., `margin-left` to `margin-inline-start`), right-hand thumb reachable CTAs, and scaleX transforms for direction-sensitive icons.

## 2. Logic Chain
1.  **State Management**: Since session cookies are tied to web browsers and `web/routers/dashboard.py` relies on sessions, the mobile app cannot use these routes directly without handling complex cookie management.
2.  **Stateless API utilization**: The `web/frontend_api.py` endpoints allow fetching stats, campaigns, and jobs using the parameter `user_id`. Therefore, we must implement a local authentication cache (e.g. `AsyncStorage` storing `user_id`) in the mobile client and supply it to the stateless APIs.
3.  **Logical Properties Translation**: Yoga layout engine in React Native handles logical mirroring natively using `marginStart`, `marginEnd`, `paddingStart`, `paddingEnd`, `start`, and `end` layout properties. Setting `supportsRTL` in `app.json` triggers native mirroring.
4.  **Font Enforcements**: React Native does not support unitless line-height scaling or generic CSS font families. We must load Cairo and Tajawal packages explicitly via `useFonts`, calculate absolute `lineHeight` values using a `1.75` multiplier, and disable `letterSpacing` (set to `0`) to satisfy connection-sensitive Arabic cursive scripts.

## 3. Caveats
*   **Backend Network Visibility**: When running in a local emulator, `localhost` points to the emulator loopback interface. Developers must use `10.0.2.2` (Android emulator bridge) or the host network IP address (physical device testing) to successfully hit the FastAPI server.
*   **Font Load Timing**: Custom fonts load asynchronously. If a view mounts and tries to render before fonts are loaded, the app will crash. Root load gates (`App.tsx`) are required.

## 4. Conclusion
We recommend initializing a clean Expo app inside `mobile/` using `npx create-expo-app@latest mobile --template blank-typescript`. The styling and logic must follow the `src/components/CustomText.tsx` and `src/services/api.ts` layouts detailed in `analysis.md` to guarantee compliance with the layout, RTL direction, typography, and stateless API requirements.

## 5. Verification Method
After initialization, verify the app's validity using:
1.  **Type Check**: Run `npx tsc` inside `mobile/` to check that the TypeScript code compiles.
2.  **Export Build test**: Execute `npx expo export` to verify that assets build and package successfully without bundle-time compiler errors.
3.  **Layout Inspection**: Inspect `mobile/app.json` to confirm `supportsRTL` is explicitly set to `true` in both iOS and Android fields.
