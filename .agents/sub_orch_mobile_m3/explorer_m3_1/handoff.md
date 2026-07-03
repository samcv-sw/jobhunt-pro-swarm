# Handoff Report - Explorer 1 (Milestone 3)

## 1. Observation
- **Backend API Endpoints**:
  - Found `/api/user/stats` (GET, line 242) in `web/frontend_api.py`:
    ```python
    @router.get("/api/user/stats")
    async def user_stats(user_id: str = ""):
    ```
  - Found `/api/campaign/list` (GET, line 431) in `web/frontend_api.py`:
    ```python
    @router.get("/api/campaign/list")
    async def campaign_list(user_id: str = ""):
    ```
  - Found `/api/jobs/user` (GET, line 481) in `web/frontend_api.py`:
    ```python
    @router.get("/api/jobs/user")
    async def jobs_user(user_id: str = "", limit: int = 20):
    ```
- **Backend Port & Host Settings**:
  - Found uvicorn initialization in `web/app_v2.py` (lines 7553-7556):
    ```python
    port = int(os.getenv("PORT", 8000))
    # ...
    uvicorn.run("web.app_v2:app", host="0.0.0.0", port=port, workers=4)
    ```
- **Package Management Style**:
  - Multiple folders contain `package-lock.json` files (e.g., `backend-node/package-lock.json`, `dashboard/package-lock.json`, `frontend/package-lock.json`), indicating `npm` is the standard tool.
- **RTL & Typography Constraints**:
  - AGENTS.md requires CSS logical properties (`margin-left` -> `margin-inline-start`, etc.), custom Arabic fonts (`Cairo`, `Tajawal` with size >= 16px, line-height 1.6 to 2.0, no letter-spacing), and scaleX icon transform for RTL (`1` for LTR, `-1` for RTL).

## 2. Logic Chain
1. The backend exposes several HTTP endpoints in `web/frontend_api.py` that can be fetched directly using REST requests. Specifically, user stats (`/api/user/stats`), campaigns (`/api/campaign/list`), and jobs (`/api/jobs/user`) are already defined and ready.
2. The server runs by default on port `8000` (`web/app_v2.py:7553`). A mobile app running on an Android Emulator needs to query host machines via `http://10.0.2.2:8000`, while iOS can use `http://localhost:8000`.
3. To build a React Native Expo app that supports RTL dynamically without breaking styles, CSS logical properties must be mapped to React Native style object properties (e.g., `paddingStart`, `marginEnd`, `start`, `end`).
4. To meet font requirements, the app must load Google Fonts (`@expo-google-fonts/cairo` and `@expo-google-fonts/tajawal`).
5. To mirror layout icons natively without relying on CSS variables, the app must determine RTL state via `I18nManager.isRTL` and apply the scaling factor `{ transform: [{ scaleX: I18nManager.isRTL ? -1 : 1 }] }`.

## 3. Caveats
- Android Emulators and iOS Simulators behave differently regarding localhost networking; the hook `useApi.ts` implements runtime checks using `Platform.OS` to avoid connection issues.
- Real-time features (like websockets in `web/routers/dashboard.py:133`) are not included in the initial REST fetching plan but can be integrated later using standard React Native `WebSocket` clients.
- If physical device testing is used, the developer must input their local computer's IP address in the configuration.

## 4. Conclusion
An Expo app with routing enabled via Expo Router should be initialized in `mobile/` via `npx create-expo-app@latest mobile --template blank-typescript`. Reusable wrappers (`ArabicText`, `ArabicTextInput`, `RTLIcon`) are key to keeping the code clean and enforcing AGENTS.md constraints.

## 5. Verification Method
- Verify the generated files (`analysis.md`) by viewing the output file in this agent folder:
  `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_mobile_m3\explorer_m3_1\analysis.md`
- Once implemented by the Implementer agent, check that:
  - App compiles and runs using `npm run android` / `npm run ios` under the `mobile/` directory.
  - Text sizes are >= 16px and Arabic rendering is readable (Cairo/Tajawal loaded).
  - RTL behaves correctly and logical style properties are used instead of hardcoded physical padding/margins.
