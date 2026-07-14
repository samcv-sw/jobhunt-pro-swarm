# Handoff Report - Next.js ISR for Static Job Pages (IMP-038)

## 1. Observation
- **Next.js Config File**: `frontend/next.config.ts`
  Line 11 contains: `output: "export"`.
  Lines 10-11:
  ```typescript
  // Comment out output: "export" to deploy to Vercel and use full Next.js SSR & Image Optimization
  output: "export",
  ```
- **Docker Frontend Build**: `Dockerfile.frontend`
  Line 35 contains:
  ```dockerfile
  CMD ["node", "node_modules/next/dist/bin/next", "start"]
  ```
- **Master Improvement List**: `IMPROVEMENTS_MASTER.md`
  Line 109-112:
  ```markdown
  ### IMP-038 — Medium — M — ⏳ TODO
  **Title**: Next.js ISR for static job pages  
  **What**: getStaticProps + revalidate:300 for job listing pages  
  **Why**: Reduces Render API hits by serving cached pages from CDN
  ```
- **App Router Directory**: `frontend/src/app`
  Contains `page.tsx` and `dashboard/page.tsx` but lacks any dedicated `/jobs` routes.

---

## 2. Logic Chain
- **Step 1 (ISR and Static Export Conflict)**: ISR relies on a server-side runtime to update page caches dynamically. When `output: "export"` is set in `next.config.ts`, Next.js compiles the project into pure static HTML/CSS/JS files and disables the server-side runtime. (Reference: Observation 1).
- **Step 2 (Deployment Conflict)**: The `Dockerfile.frontend` uses `next start` as the server startup command (Reference: Observation 2). Executing `next start` on a project built with `output: "export"` crashes at runtime because Next.js expects a Node.js server build directory which is missing in static exports.
- **Step 3 (App Router ISR Migration)**: The improvement item mentions `getStaticProps` which is a legacy Next.js Pages Router feature (Reference: Observation 3). Since the frontend codebase uses App Router (Reference: Observation 4), ISR must be designed using async Server Component fetches and page segment configuration (such as `export const revalidate = 300`).
- **Conclusion**: To implement IMP-038, `output: "export"` must be commented out or removed in `next.config.ts`. The new static job listing routes can then be created using segment-level properties and standard fetch-level revalidation configurations.

---

## 3. Caveats
- **API Accessibility**: Dynamic paths returned by `generateStaticParams` are evaluated at build time. Therefore, during compilation, the backend API (`NEXT_PUBLIC_API_URL` or fallback) must be online. If the API is unreachable, the build will compile without pre-rendering paths (empty paths array), falling back to on-demand generation on the first user request.
- **Image Optimization**: Removing `output: "export"` enables the default Next.js image optimization API. The config currently sets `unoptimized: true`. If standard image optimization is desired, this property can be removed, which will increase node memory/CPU usage.

---

## 4. Conclusion
We proposed a concrete implementation strategy written to `C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m3\explorer_2\analysis.md`.
The key requirements are:
1. Comment out `output: "export"` in `frontend/next.config.ts`.
2. Create the App Router folders `frontend/src/app/jobs/page.tsx` and `frontend/src/app/jobs/[id]/page.tsx`.
3. Use the page segment config `export const revalidate = 300` and `export const dynamicParams = true` to govern ISR behavior.
4. Pre-render existing jobs at build time using `generateStaticParams` querying the FastAPI endpoint `/api/v1/jobs`.

---

## 5. Verification Method
To verify the implementation once applied:
1. **Build Verification**: Run `npm run build` inside `frontend`. Ensure that it completes successfully, outputting Server Components and static routes with the `○` (Static) or `●` (SSG/ISR) symbols instead of static file output errors.
2. **Server Verification**: Run `npm run start` and verify that the Node.js production server starts without throwing static export runtime exceptions.
3. **ISR Cache Verification**: 
   - Add a new job to the database backend.
   - Load the `/jobs` page: the new job should not appear immediately due to the cache.
   - Wait 300 seconds (5 minutes) and reload: the cache invalidation triggers in the background.
   - Reload a second time: the new job should now be rendered on the page.
