# Handoff Report — explorer_1 (IMP-037 & IMP-101)

## 1. Observation

Direct observations made from the workspace files:

- **`frontend/package.json`**:
  - React version is `"react": "19.2.4"` (line 14) and Next.js is `"next": "16.2.9"` (line 12).
  - DevDependencies include `"typescript": "^5"` (line 25).
  - Script for building is `"build": "node node_modules/next/dist/bin/next build --webpack"` (line 7).
- **`frontend/next.config.ts`**:
  - The configuration exports a PWA-wrapped object: `export default withPWA(nextConfig);` (line 20).
  - PWA config is instantiated via CommonJS `require`: `const withPWA = require('next-pwa')({...})` (line 1).
- **`frontend/src/app/page.tsx`**:
  - Implements a live WebSocket connection on mount: `ws = new WebSocket(`${protocol}//${host}/api/v1/ws`);` (line 75).
  - Resolves language logic using `const { isArabic, toggleLocale } = useLocale();` (line 18).
- **`frontend/src/app/dashboard/page.tsx`**:
  - Imports SQLite queries: `import { runLocalQuery } from "../db/wasm-db";` (line 5).
  - Dispatches query on mount: `const campaignsQuery = await runLocalQuery("SELECT * FROM local_campaigns;");` (line 89).
- **`frontend/src/app/db/wasm-db.ts`**:
  - Injects SQL.js dynamically by creating a document script tag: `const script = document.createElement("script"); script.src = SQLITE_CDN;` (lines 29-30).
  - Interacts with `navigator.storage` for OPFS (lines 45-53, 116-123).

---

## 2. Logic Chain

1. **Windows Command Compatibility**: Because the target OS is Windows, standard POSIX variable setting like `ANALYZE=true next build` fails depending on the active terminal shell. To ensure reliability for the user, `cross-env` must be utilized for setting the `ANALYZE` environment flag (supported by Observation in `package.json` running Webpack builds).
2. **Configuration Wrapping**: The bundle analyzer wrapper (`withBundleAnalyzer`) returns a function that modifies a Next.js configuration. Because the configuration is already wrapped with `withPWA`, the wrapper must chain both functions to return `withBundleAnalyzerConfig(withPWA(nextConfig))` (supported by Observation in `next.config.ts`).
3. **Rust-based Compiler Integration**: The application uses TypeScript (`typescript: ^5`). Standard Jest configurations for TypeScript projects require transpilers like `ts-jest` or Babel setup. However, `next/jest` natively utilizes Next's built-in Rust compiler (SWC), resolving aliases like `@/*` without additional translation config (supported by Observation in `package.json` and `tsconfig.json`).
4. **WebSocket Reference Errors**: The `Home` page instantiates `new WebSocket()` inside `useEffect` on component mount. Since JSDOM does not provide a global `WebSocket` definition, running snapshot tests on the page will throw `ReferenceError: WebSocket is not defined`. Therefore, a global mock for `WebSocket` must be declared in `jest.setup.ts` (supported by Observation in `page.tsx`).
5. **SQLite/Wasm & CDN Isolation**: The client database engine (`wasm-db.ts`) queries the browser's OPFS and dynamically appends script tags loading from CDN URLs. Running this in JSDOM will crash or hang during test suites. Therefore, unit and snapshot tests of pages running Wasm DB queries (e.g. `Dashboard`) must mock `@/app/db/wasm-db` (supported by Observation in `wasm-db.ts` and `dashboard/page.tsx`).

---

## 3. Caveats

- We assumed that `npm` is the project's primary package manager due to the presence of `frontend/package-lock.json` and absence of `yarn.lock` or `pnpm-lock.yaml`.
- Webpack (`--webpack`) is explicitly required in `npm run build` which is compatible with `@next/bundle-analyzer` since it is a Webpack-specific plugin. If Next.js moves to Turbopack in the future, standard `@next/bundle-analyzer` configurations will need updating to support Turbopack visualizer tooling.

---

## 4. Conclusion

The implementation strategy is clear and fully designed in `analysis.md` inside this directory:
- **IMP-037**: Install `cross-env` and `@next/bundle-analyzer`. Wrap configurations in `next.config.ts`. Add script `"analyze": "cross-env ANALYZE=true npm run build"`.
- **IMP-101**: Install Jest, JSDOM, and React Testing Library devDependencies. Implement `jest.config.mjs` and `jest.setup.ts` featuring the global `WebSocket` and `matchMedia` polyfills/mocks. Mock `@/app/db/wasm-db` module specifically inside dashboard testing suites. Create snapshot tests for `SkeletonLoader.tsx`, `app/page.tsx`, and `app/dashboard/page.tsx`.

---

## 5. Verification Method

To verify the setup:

1. **Verify Bundle Analyzer**:
   - Run `npm run analyze` from the `frontend` folder.
   - Assert that the build completes successfully and visual reports are outputted to `frontend/.next/analyze/client.html` and `frontend/.next/analyze/server.html`.
2. **Verify Jest Snapshot Tests**:
   - Run `npm run test` (or `npx jest`) from the `frontend` folder.
   - Confirm that Jest successfully executes all three test suites: `SkeletonLoader.test.tsx`, `page.test.tsx`, and `dashboard/page.test.tsx` and generates snapshot files matching the components' layouts.
