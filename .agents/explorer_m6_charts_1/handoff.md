# Handoff Report: Milestone 6 (Next.js Dashboard Analytics)

This report details the codebase findings, logic chain, and implementation recommendations for Milestone 6 (Next.js Dashboard Analytics), focusing on integrating interactive charts/statistics for job search success metrics, email open rates, and ATS score history.

---

## 1. Observation

During read-only codebase exploration, the following locations and structures were analyzed:

### A. Next.js Frontend Codebase
1. **Frontend Directory Structure**: Located at `frontend/`. Contains Next.js (version `16.2.9`), React (version `19.2.4`), and Tailwind CSS (version `4`).
2. **Dashboard File**: Located at `frontend/src/app/dashboard/page.tsx` (624 lines).
   - Currently, it utilizes a client-side WebAssembly SQLite engine (`sql.js`) to load records via the browser's **Origin Private File System (OPFS)**.
   - It contains a static, glassmorphic line chart drawn inside an **inline SVG element** (lines 476–586) that compares weekly `Scraped Jobs` vs `Submitted Apps` using mock hardcoded values:
     ```typescript
     const chartDays = isArabic
       ? ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
       : ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"];
     const chartScrapeValues = [65, 84, 92, 71, 110, 125, 95];
     const chartAppValues = [60, 78, 88, 64, 105, 120, 90];
     ```
3. **Frontend Browser Database Client**: Located at `frontend/src/app/db/wasm-db.ts` (152 lines).
   - Currently initializes local tables: `local_cv_profiles`, `local_campaigns`, and `local_sync_queue`.
   - Lacks tables to record individual jobs or applications (e.g., `local_jobs` or `local_applications`).
4. **Dependencies**: In `frontend/package.json`, there are no charting libraries installed:
   ```json
   "dependencies": {
     "next": "16.2.9",
     "next-pwa": "^5.6.0",
     "react": "19.2.4",
     "react-dom": "19.2.4"
   }
   ```

### B. Backend Data & Core Engines
1. **Database Schema**: Querying the local SQLite databases (`core/saas_v2.db` and `data/jobhunt_saas_v2.db`) reveals existing tables containing the requested metrics:
   - **`jobs` Table**:
     ```sql
     CREATE TABLE jobs (
         id INTEGER NOT NULL,
         job_id VARCHAR(64) NOT NULL,
         company VARCHAR(255) NOT NULL,
         title VARCHAR(255) NOT NULL,
         email VARCHAR(255) NOT NULL,
         location VARCHAR(255),
         salary VARCHAR(100),
         url TEXT,
         source VARCHAR(50),
         snippet TEXT,
         status VARCHAR(50) NOT NULL,    -- Tracks application status (e.g., applied, interview, offer)
         match_score NUMERIC(5, 2),       -- Groq ATS compatibility score
         response_type VARCHAR(50),
         applied_at VARCHAR(50),
         responded_at VARCHAR(50),
         created_at DATETIME,
         updated_at DATETIME,
         PRIMARY KEY (id),
         UNIQUE (job_id)
     )
     ```
   - **`applications` Table**:
     ```sql
     CREATE TABLE applications (
         id INTEGER NOT NULL,
         job_id VARCHAR(64) NOT NULL,
         company VARCHAR(255) NOT NULL,
         title VARCHAR(255) NOT NULL,
         email VARCHAR(255) NOT NULL,
         cover_letter TEXT,
         cv_path TEXT,
         provider VARCHAR(50),
         tracking_id VARCHAR(32),
         status VARCHAR(50) NOT NULL,
         followup_count INTEGER NOT NULL,
         opened BOOLEAN NOT NULL,         -- Boolean flag for tracking email opens
         clicked BOOLEAN NOT NULL,
         responded BOOLEAN NOT NULL,
         response_type VARCHAR(50),
         sent_at DATETIME,
         opened_at DATETIME,
         responded_at DATETIME,
         PRIMARY KEY (id)
     )
     ```
2. **Analytics Engine**: Located at `core/analytics.py`.
   - Implements SQL queries in `Analytics.get_dashboard_data()` and `Analytics.get_conversion_funnel()` to aggregate open rates, response rates, and application pipelines:
     ```python
     stats_query = """
         SELECT
             (SELECT COUNT(*) FROM applications) as total,
             (SELECT COUNT(*) FROM applications WHERE opened = 1) as opened,
             (SELECT COUNT(*) FROM applications WHERE responded = 1) as responded
     """
     ```
3. **FastAPI Endpoints**: In `backend/main.py`, multiple analytics endpoints exist (e.g. `scrapers/health`, `/api/v1/analytics/export`, `/api/v1/analytics/tone-performance`), but there is no endpoint that exposes the general funnel and open-rate aggregates from `core/analytics.py` to the frontend dashboard.

---

## 2. Logic Chain

The step-by-step reasoning maps these observations directly to the recommended implementation choices:

1. **Required Charts Mapping**:
   - **Job Search Success Metrics**: Can be visualized via a **Conversion Funnel** or a **Bar Chart** showing status frequencies: `scraped` $\rightarrow$ `applied` $\rightarrow$ `interview` $\rightarrow$ `offer`. This aligns with the database's `jobs.status` column and the existing `get_conversion_funnel` analytics backend logic.
   - **Email Open Rates**: Needs a **Time-Series Area Chart** or a **Circular Gauge** showing $\frac{\text{opened}}{\text{sent\_emails}}$ over time. This directly leverages `applications.opened` and `applications.sent_at`.
   - **ATS Score History**: Requires a **Line Chart** or **Scatter Plot** showing `jobs.match_score` (Y-axis) plotted against `jobs.created_at` or `applied_at` (X-axis).
2. **First-Class Charting Architecture Option**:
   - *Option A: Zero-Dependency Interactive SVG Component*. Extends the existing SVG code in the Next.js page component to compute hover mouse coordinates, handle tooltips, and draw paths dynamically. Fits the project's zero-dependency, zero-operating-cost edge deployment pattern.
   - *Option B: Recharts Library Integration*. Requires installing `recharts` package. Fits standard Next.js dashboards and provides responsive, visually polished chart elements with built-in tooltips and zoom functions.
3. **RTL & Localization Compliance**:
   - The React state relies on `isArabic` from `locale-context.tsx`. Labels, dates, and tooltip values on the interactive charts must dynamically load English vs. Arabic counterparts.
4. **Data Delivery Strategy**:
   - Instead of duplicating the entire database schema into the client-side WebAssembly SQLite database, the Next.js frontend should perform a `fetch()` to a new FastAPI route. This avoids the overhead of replicating the `jobs` and `applications` tables onto browser local storage.

---

## 3. Caveats

- **React 19 Compatibility**: Recharts sometimes requires `--legacy-peer-deps` or specific v2/v3-alpha versions to work smoothly with React 19. Ensure peer dependencies are validated during npm installation.
- **Edge Deployment Cold Starts**: Because Neon PostgreSQL database instances suspend when idle, initial page queries to compile telemetry might experience standard latency up to 15 seconds unless queried through a caching layer.

---

## 4. Conclusion & Proposed Implementation Plan

We recommend implementing the Dashboard Analytics in two parts: exposing the backend data and building the frontend interactive charts.

### Part A: Expose Backend Telemetry Endpoint
Add the following endpoint to `backend/main.py` to provide the raw numbers:

```python
@app.get("/api/v1/analytics/dashboard-summary", dependencies=[Depends(verify_jwt)])
async def get_dashboard_summary(payload: dict = Depends(verify_jwt)):
    """Fetch dashboard analytics summary for charts and statistics."""
    from core.analytics import Analytics
    import core.pg_sqlite_shim as sqlite3
    
    analytics_mgr = Analytics()
    data = analytics_mgr.get_dashboard_data()
    funnel = analytics_mgr.get_conversion_funnel()
    
    # Also fetch ATS match score history over time
    ats_history = []
    try:
        with sqlite3.connect(analytics_mgr.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT title, company, match_score, created_at FROM jobs "
                "WHERE match_score IS NOT NULL AND user_id = ? "
                "ORDER BY created_at ASC LIMIT 50", (payload.get("sub"),)
            ).fetchall()
            ats_history = [dict(r) for r in rows]
    except Exception:
        # Fallback to general history
        with sqlite3.connect(analytics_mgr.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT title, company, match_score, created_at FROM jobs "
                "WHERE match_score IS NOT NULL ORDER BY created_at ASC LIMIT 50"
            ).fetchall()
            ats_history = [dict(r) for r in rows]

    return {
        "success": True,
        "funnel": funnel,
        "response_rates": data["response_rates"],
        "ats_history": ats_history
    }
```

---

### Part B: Frontend Interactive Charts Options

#### Option 1: Zero-Dependency Interactive SVG Chart (Self-Contained)
Modify `frontend/src/app/dashboard/page.tsx` to handle dynamic mouse hovers over the SVG paths. This requires no extra package installations:

```tsx
"use client";

import React, { useState } from "react";

// Types for data points
interface DataPoint {
  label: string;
  value: number;
}

export function InteractiveSVGChart({ isArabic }: { isArabic: boolean }) {
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; val: number; label: string } | null>(null);

  // ATS score history mock values (replacing mock static variables)
  const data: DataPoint[] = [
    { label: isArabic ? "الاثنين" : "Mon", value: 65 },
    { label: isArabic ? "الثلاثاء" : "Tue", value: 72 },
    { label: isArabic ? "الاربعاء" : "Wed", value: 68 },
    { label: isArabic ? "الخميس" : "Thu", value: 85 },
    { label: isArabic ? "الجمعة" : "Fri", value: 89 },
    { label: isArabic ? "السبت" : "Sat", value: 92 },
    { label: isArabic ? "الأحد" : "Sun", value: 94 },
  ];

  const width = 500;
  const height = 200;
  const padding = 40;

  // Coordinate mapper helpers
  const getX = (index: number) => padding + (index * (width - padding * 2)) / (data.length - 1);
  const getY = (value: number) => height - padding - (value * (height - padding * 2)) / 100;

  // Build SVG path
  const points = data.map((d, i) => `${getX(i)},${getY(d.value)}`).join(" L ");
  const linePath = `M ${points}`;
  const areaPath = `${linePath} L ${getX(data.length - 1)},${height - padding} L ${getX(0)},${height - padding} Z`;

  return (
    <div className="relative p-4 bg-zinc-950/40 border border-zinc-900 rounded-xl">
      <svg viewBox={`0 0 ${width} ${height}`} className="overflow-visible w-full h-auto">
        <defs>
          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#D4AF37" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid Lines */}
        <line x1={padding} y1={getY(0)} x2={width - padding} y2={getY(0)} stroke="rgba(255,255,255,0.1)" />
        <line x1={padding} y1={getY(50)} x2={width - padding} y2={getY(50)} stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
        <line x1={padding} y1={getY(100)} x2={width - padding} y2={getY(100)} stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />

        {/* Area and Line */}
        <path d={areaPath} fill="url(#chartGradient)" />
        <path d={linePath} fill="none" stroke="#D4AF37" strokeWidth="2.5" />

        {/* Interactive Data Points */}
        {data.map((d, i) => {
          const cx = getX(i);
          const cy = getY(d.value);
          return (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r="6"
              fill="#D4AF37"
              stroke="#060608"
              strokeWidth="2"
              className="cursor-pointer transition hover:scale-150"
              onMouseEnter={() => setHoveredPoint({ x: cx, y: cy, val: d.value, label: d.label })}
              onMouseLeave={() => setHoveredPoint(null)}
            />
          );
        })}
      </svg>

      {/* State-driven Tooltip overlay */}
      {hoveredPoint && (
        <div
          className="absolute bg-zinc-900 border border-zinc-800 text-xs p-2 rounded shadow-md pointer-events-none"
          style={{ left: `${(hoveredPoint.x / width) * 100}%`, top: `${(hoveredPoint.y / height) * 100 - 15}%`, transform: "translate(-50%, -100%)" }}
        >
          <div className="font-bold">{hoveredPoint.label}</div>
          <div className="text-amber-400">Score: {hoveredPoint.val}%</div>
        </div>
      )}
    </div>
  );
}
```

---

#### Option 2: Recharts Library Integration (Modern Dashboard Layout)
Install recharts using the command line:
```bash
npm install recharts --legacy-peer-deps
```

Create a reusable interactive chart component at `frontend/src/components/DashboardCharts.tsx`:

```tsx
"use client";

import React from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from "recharts";

// Success funnel data format
interface FunnelData {
  stage: string;
  count: number;
}

// ATS history data format
interface ATSHistory {
  date: string;
  score: number;
}

export function JobSuccessChart({ data, isArabic }: { data: FunnelData[]; isArabic: boolean }) {
  return (
    <div className="w-full h-[250px] bg-zinc-950/40 p-4 border border-zinc-900 rounded-xl">
      <h3 className="text-sm font-bold text-white mb-2">
        {isArabic ? "قمع التوظيف والنجاح" : "Job Application Funnel"}
      </h3>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f1f2e" />
          <XAxis dataKey="stage" stroke="#71717a" />
          <YAxis stroke="#71717a" />
          <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a" }} />
          <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ATSScoreHistoryChart({ data, isArabic }: { data: ATSHistory[]; isArabic: boolean }) {
  return (
    <div className="w-full h-[250px] bg-zinc-950/40 p-4 border border-zinc-900 rounded-xl">
      <h3 className="text-sm font-bold text-white mb-2">
        {isArabic ? "تاريخ تقييم ATS الذكي" : "ATS Match Score History"}
      </h3>
      <ResponsiveContainer width="100%" height="90%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#D4AF37" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#D4AF37" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f1f2e" />
          <XAxis dataKey="date" stroke="#71717a" />
          <YAxis domain={[0, 100]} stroke="#71717a" />
          <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a" }} />
          <Area type="monotone" dataKey="score" stroke="#D4AF37" fillOpacity={1} fill="url(#colorScore)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
```

---

## 5. Verification Method

1. **Verify Backend Analytics Schema and Endpoint**:
   Ensure python tests pass and verify that the API serves proper JSON data by running:
   ```bash
   pytest tests/
   ```
   Submit a test query to the newly created endpoint:
   ```bash
   curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/analytics/dashboard-summary
   ```

2. **Verify Frontend UI Integration**:
   Start the Next.js development server:
   ```bash
   npm run dev
   ```
   Navigate to `/dashboard` and check the browser dev tools for:
   - Zero console warnings regarding SVG DOM mismatches.
   - Fluid responsiveness when toggling between English (LTR) and Arabic (RTL) mode.
