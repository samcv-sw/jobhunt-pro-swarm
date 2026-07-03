# JobHunt Pro Frontend — Build Constraints & Dependencies Investigation

This report documents the investigation of the Next.js project under `frontend/`, outlining its dependencies, configuration, build script execution, and potential roadblocks.

---

## 1. Dependency Tree & Package Analysis
The frontend is a minimal, dependency-optimized Next.js workspace designed for performance and zero SaaS cost.

### Core Framework & Runtime
*   **Next.js**: `16.2.9` (Turbopack-enabled release)
*   **React**: `19.2.4`
*   **React DOM**: `19.2.4`

### Styling & CSS Ecosystem
*   **Tailwind CSS**: `^4` (Tailwind v4 is used)
*   **PostCSS / PostCSS Loader**: `@tailwindcss/postcss ^4`

### Development & Tooling
*   **TypeScript**: `^5`
*   **ESLint**: `^9`
*   **ESLint Next Config**: `eslint-config-next 16.2.9`
*   **TypeScript Types**: Node, React, and React-DOM version-matched types.

### Key Observation: Zero UI / Utility Dependencies
*   **No UI Component Packages**: There are **no external UI component libraries** (e.g., Radix, Shadcn UI, Headless UI, Material UI, Ant Design). All UI components, buttons, inputs, and modals are built using native HTML elements styled with custom utility classes.
*   **No Icon Libraries**: There are **no icon packages** (e.g., Lucide React, FontAwesome). Emojis and inline CSS/SVG are utilized instead.
*   **No Chart Libraries**: There are **no visual graphing/chart libraries** (e.g., Recharts, Chart.js).
*   **No Tailwind Utility Libraries**: Helper libraries like `tailwind-merge`, `clsx`, or `class-variance-authority` are absent.
*   **Dynamic SQLite Client**: The application uses SQLite in the browser via WebAssembly (`frontend/src/app/db/wasm-db.ts`). To keep compilation/bundle sizes small and prevent native binary compilation issues, it **dynamically injects the SQLite JavaScript client and WASM binary at runtime** via CDN (`cdnjs.cloudflare.com` for `sql-wasm.js` and `sql-wasm.wasm`).

---

## 2. Configurations & File Analysis

### Next.js Configuration (`frontend/next.config.ts`)
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
```
*   `output: "export"`: Next.js is configured to build a static website (HTML/CSS/JS export) inside the `out/` folder rather than running a Node.js SSR server.
*   `images: { unoptimized: true }`: Essential configuration to bypass Next.js image optimization runtime requirements, preventing build failures during static export.

### Tailwind Configuration
*   **No `tailwind.config.js` or `tailwind.config.ts` exists**: Tailwind v4 is configured entirely within `frontend/src/app/globals.css` using CSS-based `@theme` directives and `@import "tailwindcss";`.
*   **PostCSS Integration**: Managed via `frontend/postcss.config.mjs` using `@tailwindcss/postcss`.

### TypeScript Configuration (`frontend/tsconfig.json`)
*   Strict mode `"strict": true` is enabled, enforcing type-safety across all components.
*   Path aliasing `@/*` is mapped to `./src/*`.
*   Uses `"moduleResolution": "bundler"` and `"module": "esnext"`.

### ESLint Configuration (`frontend/eslint.config.mjs`)
*   Uses Flat Config setup.
*   Extends `eslint-config-next/core-web-vitals` and `eslint-config-next/typescript`.
*   Overrides global ignores to skip linting in `.next/**`, `out/**`, `build/**`, and `next-env.d.ts`.

---

## 3. Build Scripts & Execution Roadblocks

### Roadblock 1: Windows CMD Path/Ampersand Splitting (`npm run build`)
*   **Issue**: Running `npm run build` from the frontend directory fails with the error:
    `Error: Cannot find module 'C:\Users\samde\Desktop\next\dist\bin\next'`
*   **Cause**: The absolute path to the workspace includes an ampersand: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\frontend`. The `node_modules/.bin/next.cmd` script resolves execution context using `%dp0%`, expanding the unquoted path, and the ampersand `&` is parsed as a CMD command separator.
*   **Resolution/Workaround**: The build must be executed by invoking Node directly on the script path:
    ```bash
    node node_modules/next/dist/bin/next build
    ```
    This bypasses the CMD shell wrapper parser and successfully generates the static files.

### Roadblock 2: Strict ESLint Failures in CI/CD Environments
*   Running `node node_modules/eslint/bin/eslint.js .` fails (exit code 1) with **11 problems (9 errors, 2 warnings)**:
    1.  **SQLite Client (`src/app/db/wasm-db.ts`)**: Contains 8 errors due to the use of `any` types (e.g. `dbInstance: any`, `Promise<any>`, `(window as any).initSqlJs`, etc.), violating `@typescript-eslint/no-explicit-any`.
    2.  **Home Page (`src/app/page.tsx`)**:
        *   Contains a critical React Hook violation (`react-hooks/set-state-in-effect`): calling `calculateShard()` (which updates state synchronously via `setIsHashing(true)`) within `useEffect` directly on initial mount.
        *   Missing dependency `calculateShard` in `useEffect` dependency array (`react-hooks/exhaustive-deps`).
        *   Unused import: `'Image'` is imported from `'next/image'` but never used.
*   *Note*: While `next build` with Turbopack compiles successfully to the `out/` folder, running ESLint will block any CI/CD validation pipelines.

### Roadblock 3: `Dockerfile.frontend` and `output: "export"` Mismatch
*   **Issue**: `Dockerfile.frontend` in the project root is built as if the frontend requires a Node.js SSR server:
    *   It executes `npm run build`
    *   It copies `/app/.next` and `/app/node_modules` into a runner image
    *   It launches the container using `CMD ["npm", "start"]` (which runs `next start`)
*   **Roadblock**: Because `next.config.ts` defines `output: "export"`, there is no SSR application inside `.next` to run. Running `next start` on a static export will crash or fail to serve files.
*   **Resolution**: The Dockerfile needs to be rewritten to copy `/app/out` into a static server container (e.g., `nginx:alpine` or `caddy:alpine`) instead of using Node.js runtime.

---

## 4. Next.js 16 Features
*   **Bundled Documentation**: In Next.js 16, documentation is version-matched and bundled inside `node_modules/next/dist/docs/`.
*   **Instant Navigations**: Supports `unstable_instant = { prefetch: 'static' }` route segment exports to enforce and validate static shell rendering.
