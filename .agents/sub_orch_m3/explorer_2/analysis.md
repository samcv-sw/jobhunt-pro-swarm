# Analysis: Next.js ISR for Static Job Pages (IMP-038)

## Executive Summary
Integrating Incremental Static Regeneration (ISR) for static job pages requires removing `output: "export"` from `next.config.ts`, as static exports lack the server-side runtime needed to process background page regeneration. This change also resolves a critical deployment conflict where `Dockerfile.frontend` is configured to run `next start` (which fails on static exports).

---

## 1. Observations

### 1.1 Next.js Configuration (`frontend/next.config.ts`)
The current Next.js configuration is set to build a fully static HTML export:
```typescript
// frontend/next.config.ts (Lines 8-18)
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Comment out output: "export" to deploy to Vercel and use full Next.js SSR & Image Optimization
  output: "export",
  trailingSlash: true,
  images: {
    // Enable WebP & AVIF for smaller image sizes on supported browsers
    formats: ['image/avif', 'image/webp'],
    unoptimized: true,
  },
};
```

### 1.2 Docker Runtime Configuration (`Dockerfile.frontend`)
The Docker setup compiles and starts the Next.js frontend using the production server runtime:
```dockerfile
# Dockerfile.frontend (Lines 33-36)
EXPOSE 3000

CMD ["node", "node_modules/next/dist/bin/next", "start"]
```

### 1.3 Target Improvement (from `IMPROVEMENTS_MASTER.md`)
The improvement is documented in `IMPROVEMENTS_MASTER.md` as follows:
```markdown
### IMP-038 — Medium — M — ⏳ TODO
**Title**: Next.js ISR for static job pages  
**What**: getStaticProps + revalidate:300 for job listing pages  
**Why**: Reduces Render API hits by serving cached pages from CDN
```
*Note: The master sheet references `getStaticProps`, which is a legacy Pages Router pattern. Since `frontend` uses the modern Next.js App Router, the implementation must use Server Component async fetching and segment/fetch-level configuration.*

---

## 2. Logic Chain

1. **ISR Technical Requirement**: ISR requires a running Node.js or Edge server to handle incoming requests, check if cache TTL has expired, initiate background regeneration of the static pages, and update the cache directory dynamically.
2. **Static Export Behavior**: Setting `output: "export"` compiles the app into a folder of raw static HTML, CSS, and JS files (`out/`). There is no Node.js backend output generated under `.next` that supports server rendering or background regeneration.
3. **Deployment Conflict**:
   - `Dockerfile.frontend` executes `next start` to boot a Node.js production server.
   - If `output: "export"` is enabled, `next start` crashes at runtime with a message stating that it cannot serve a statically exported site.
4. **Conclusion**: To resolve the deployment conflict and enable ISR, `output: "export"` must be commented out or removed from `next.config.ts`.

---

## 3. Design and Implementation Strategy for IMP-038

Since the application uses the Next.js App Router (`frontend/src/app`), we should define the static job listing and detail pages as Server Components utilizing route segment properties and the Next.js extended `fetch` API.

### 3.1 Directory Structure
We propose creating the following routes inside the Next.js frontend:
```
frontend/src/app/
├── jobs/
│   ├── page.tsx          # Job Listings directory page (ISR)
│   └── [id]/
│       └── page.tsx      # Job Detail pages (Dynamic Route, ISR)
```

### 3.2 Job Listings Page Implementation Design (`frontend/src/app/jobs/page.tsx`)
This page displays all scraped jobs. We use a route segment config to revalidate the page cache every 300 seconds (5 minutes).

```typescript
import Link from "next/link";

export const revalidate = 300; // Segment-level revalidation TTL in seconds

interface Job {
  id: number;
  company_name: string;
  job_title: string;
  source: string;
  scraped_at: string;
}

async function getJobs(): Promise<Job[]> {
  const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  // The fetch call inherits the segment-level revalidate or can declare it explicitly:
  const res = await fetch(`${apiHost}/api/v1/jobs`, {
    next: { revalidate: 300 }
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch jobs from API: ${res.statusText}`);
  }
  const data = await res.json();
  return data.jobs || [];
}

export default async function JobsListingPage() {
  const jobs = await getJobs();

  return (
    <div className="flex flex-col p-6 md:p-12 bg-[#060608] min-h-screen text-white">
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold text-white">
          <span className="gold-glow-text">Open Positions</span>
        </h1>
        <p className="text-sm text-zinc-400 mt-1">Statically cached job listings (revalidated every 5m)</p>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {jobs.map((job) => (
          <div key={job.id} className="glass-panel p-6 flex flex-col justify-between border border-zinc-800/40 rounded-xl bg-zinc-950/50">
            <div>
              <span className="text-xs text-zinc-500 uppercase tracking-widest block mb-2">{job.source}</span>
              <h2 className="text-lg font-bold text-white mb-1">{job.job_title}</h2>
              <p className="text-sm text-zinc-400">{job.company_name}</p>
            </div>
            <div className="mt-4 pt-4 border-t border-zinc-800/40 flex justify-between items-center">
              <span className="text-xs text-zinc-500">Scraped: {job.scraped_at}</span>
              <Link href={`/jobs/${job.id}`} className="text-sm font-bold text-[#D4AF37] hover:underline">
                View Details →
              </Link>
            </div>
          </div>
        ))}
      </main>
    </div>
  );
}
```

### 3.3 Job Detail Page Implementation Design (`frontend/src/app/jobs/[id]/page.tsx`)
This page handles individual job detail rendering. We pre-generate common paths at build time using `generateStaticParams`, and fallback to on-demand generation with a 5-minute cache TTL.

```typescript
import { notFound } from "next/navigation";
import Link from "next/link";

export const revalidate = 300; // Segment-level revalidation TTL in seconds
export const dynamicParams = true; // Fallback to on-demand render for paths not pre-generated

interface JobDetail {
  id: number;
  company_name: string;
  job_title: string;
  source: string;
  scraped_at: string;
  description_snippet?: string;
  full_description?: string;
}

// Fetch paths to pre-render during next build
export async function generateStaticParams() {
  const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${apiHost}/api/v1/jobs`);
    if (!res.ok) return [];
    const data = await res.json();
    const jobs = data.jobs || [];
    return jobs.map((job: any) => ({
      id: job.id.toString(),
    }));
  } catch (error) {
    console.error("Error generating static params for jobs:", error);
    return [];
  }
}

async function getJobDetail(id: string): Promise<JobDetail | null> {
  const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    // Under ISR, this fetch is cached and automatically revalidated
    const res = await fetch(`${apiHost}/api/v1/jobs/${id}`, {
      next: { revalidate: 300 }
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.job;
  } catch (error) {
    console.error(`Error fetching details for job ID ${id}:`, error);
    return null;
  }
}

export default async function JobDetailPage({ params }: { params: { id: string } }) {
  const job = await getJobDetail(params.id);

  if (!job) {
    notFound();
  }

  return (
    <div className="flex flex-col p-6 md:p-12 bg-[#060608] min-h-screen text-white">
      <header className="mb-6">
        <Link href="/jobs" className="text-sm text-zinc-400 hover:text-white flex items-center gap-1">
          ← Back to All Jobs
        </Link>
      </header>

      <main className="glass-panel p-8 border border-zinc-800/40 rounded-xl bg-zinc-950/50 max-w-3xl">
        <div className="border-b border-zinc-800/40 pb-6 mb-6">
          <span className="text-xs text-[#D4AF37] font-semibold uppercase tracking-widest block mb-2">
            {job.source}
          </span>
          <h1 className="text-3xl font-extrabold text-white mb-2">{job.job_title}</h1>
          <p className="text-lg text-zinc-300">{job.company_name}</p>
        </div>

        <div className="text-zinc-400 text-sm leading-[1.8] space-y-4">
          <h3 className="text-white font-bold text-md">Job Description</h3>
          <p className="whitespace-pre-wrap">
            {job.full_description || job.description_snippet || "No description provided."}
          </p>
        </div>

        <footer className="border-t border-zinc-800/40 mt-8 pt-4 text-xs text-zinc-500 flex justify-between">
          <span>Job ID: {job.id}</span>
          <span>Scraped on: {job.scraped_at}</span>
        </footer>
      </main>
    </div>
  );
}
```

---

## 4. Caveats

- **API Availability during Build**: `generateStaticParams` queries the FastAPI backend (`/api/v1/jobs`) at build time. Therefore, the backend API must be active and accessible during the Next.js application build step. If the backend is down during building, `generateStaticParams` will fall back to an empty array `[]` (meaning all pages will be generated on-demand when requested by the user, which is a supported fallback but raises first-load response times).
- **Environment URLs**: Docker environments resolve hostnames using internal service names (e.g. `http://app:8000`), whereas local development uses `http://localhost:8000`. The build environment must correctly configure `NEXT_PUBLIC_API_URL` to match the target environment.
- **Image Optimization**: Removing `output: "export"` enables the default Next.js Image Optimization API. The current configuration has `unoptimized: true`. If dynamic image optimization is desired, `unoptimized` can be removed, but this will consume memory/CPU on the frontend container.

---

## 5. Conclusion

1. **Required config changes**: Remove or comment out `output: "export"` in `frontend/next.config.ts`.
2. **ISR Routes implementation**: Build two routes `frontend/src/app/jobs/page.tsx` and `frontend/src/app/jobs/[id]/page.tsx` utilizing App Router async Server Component fetch configuration.
3. **Deployment safety**: Doing so fixes the runtime crash in `Dockerfile.frontend` that happens when `next start` is executed on a static-export build.

---

## 6. Verification Method

To verify the proposed implementation safely without breaking production:

1. **Config Modification verification**:
   Comment out `output: "export"` in `frontend/next.config.ts`.
2. **Build test**:
   Run the following commands inside the `frontend` folder:
   ```pwsh
   npm run build
   ```
   Verify that the output format reports static generation (`○` or `●` symbols for ISR/SSG pages) and produces a `.next/` directory structure containing the server runtime outputs, instead of an `out/` folder.
3. **Local Server execution**:
   Run the production preview command:
   ```pwsh
   npm run start
   ```
   Ensure the server starts up on port 3000 without crashing with static-export runtime errors.
4. **ISR functionality verify**:
   - Access the `/jobs` page.
   - Insert a mock job record directly into the backend database.
   - Refresh the page immediately: the mock job should **not** appear (as you receive the cached static page).
   - Wait 300 seconds (5 minutes) and refresh the page: Next.js will serve the cached page but trigger a background fetch.
   - Refresh the page a second time: the new mock job should now be visible on the list.
