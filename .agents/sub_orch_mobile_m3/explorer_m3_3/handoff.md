# Handoff Report: Milestone 1 - Initialize Expo App

## 1. Observation
1. **Backend Endpoints**: We inspected `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\frontend_api.py` and identified the key user and campaign REST endpoints:
   - User stats: `@router.get("/api/user/stats")` on line 242.
   - User jobs: `@router.get("/api/jobs/user")` on line 481.
   - Campaigns list: `@router.get("/api/campaign/list")` on line 431.
   - Create campaign: `@router.post("/api/campaign/create")` on line 385.
   - Registration fast: `@router.post("/api/register-fast")` on line 121.
2. **Workspace Status**: We ran a file search for `**/mobile/**` and confirmed that no `mobile/` directory currently exists in the workspace.
3. **Styling Rules**: We read the user guidelines for Gulf region ergonomics and RTL/Arabic layouts, specifying:
   - CSS Logical Properties (e.g. `padding-right` -> `padding-inline-end`).
   - Arabic Typography: fonts like Cairo/Tajawal, min size 14px, recommended >= 16px, line-height 1.6-2.0, no letter spacing on Arabic.
   - Culturally appropriate colors: Success (Green), Luxury (Black/Gold), Trust (Blue), strict error (Red).
   - Icons: transform scaleX (-1 in RTL, 1 in LTR).

## 2. Logic Chain
1. **Network Connectivity**: Because React Native runs on emulators/simulators or physical devices, connecting to `localhost:8000` directly fails on Android emulators (which view the host machine as `10.0.2.2`). Thus, a utility function in `src/api/client.ts` must dynamically switch the base URL between `10.0.2.2:8000` (Android) and `localhost:8000` (iOS/web) in development.
2. **Logical Styles in React Native**: React Native's StyleSheet layout engine doesn't support CSS logical property names directly (`padding-inline-start`), but it natively supports physical logical properties like `paddingStart`, `paddingEnd`, `marginStart`, `marginEnd`, `start`, and `end`. These are automatically handled by the Yoga layout engine according to `I18nManager.isRTL`.
3. **RTL Dynamic Re-rendering**: Layouts in React Native are locked upon initial bundle load. If the user changes language dynamically, changing `I18nManager.forceRTL()` requires wrapping with `expo-updates`'s `Updates.reloadAsync()` to re-render the app bundle with the flipped geometry.
4. **Font Integration**: Google Fonts must be loaded asynchronously during root layout rendering. We use `useFonts` from `@expo-google-fonts/cairo` and `@expo-google-fonts/tajawal` to prevent the app from displaying incorrect fallback fonts.

## 3. Caveats
* **No Active Simulation**: The proposed configurations and code templates have not been run on an active emulator since this is a read-only investigation phase.
* **Production API Base URL**: The production base URL in the API client is configured as a placeholder (`https://api.yourjobhuntapp.com`) and must be updated with the actual domain once the FastAPI backend is deployed to production.

## 4. Conclusion
* Initialize the React Native Expo app in `mobile/` using `npx create-expo-app@latest mobile --template blank-typescript`.
* The application should use custom, logical wrapper components (`RTLText`, `RTLTextInput`, and `DirectionalIcon`) to adhere to the Arabic layout rules automatically, rather than relying on developers to manually adjust styling rules per element.

## 5. Verification Method
1. **Initialization Verification**: Navigate to the root directory and run:
   ```bash
   npx create-expo-app@latest mobile --template blank-typescript
   ```
   Check that `mobile/package.json` is generated successfully.
2. **Font Verification**: Run `npx expo start` inside the `mobile/` folder and verify that the Cairo/Tajawal fonts load correctly during startup.
3. **API Integration Verification**: Run the FastAPI backend (`python web/app_v2.py` or similar command) and call the health check endpoint `/api/cloud-health` from the mobile app's simulator to confirm network routing.
