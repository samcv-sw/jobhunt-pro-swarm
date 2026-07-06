## 2026-07-06T08:35:54Z
You are a worker agent assigned to fix a Next.js production build issue.

Your objective:
1. Locate `frontend/src/app/layout.tsx` and `frontend/src/app/root-html.tsx`.
2. Modify `frontend/src/app/layout.tsx` to remove the `RootHtml` client component wrapper, and instead render the standard `<html>` and `<body>` tags directly inside the server component layout. The `LocaleProvider` should wrap only the children/body content.
Here is the desired structure for `frontend/src/app/layout.tsx`:
```tsx
import type { Metadata } from "next";
import { Cairo, Tajawal } from "next/font/google";
import "./globals.css";
import { LocaleProvider } from "./locale-context";

const cairo = Cairo({
  variable: "--font-cairo",
  subsets: ["latin", "arabic"],
  display: "swap",
});

const tajawal = Tajawal({
  variable: "--font-tajawal",
  subsets: ["arabic"],
  weight: ["400", "500", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "JobHunt Pro — نظام التقديم الذكي",
  description: "منصة SaaS لأتمتة التقديم على الوظائف بالذكاء الاصطناعي — تقديم تلقائي، رسائل مخصصة، وتتبع مستمر.",
  keywords: ["job hunt", "AI", "automated applications", "cover letter", "SaaS", "توظيف", "سيرة ذاتية"],
  openGraph: {
    title: "JobHunt Pro",
    description: "AI-Powered Automated Job Application Platform",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ar"
      dir="rtl"
      className={`${cairo.variable} ${tajawal.variable} antialiased dark`}
      style={{ blockSize: "100%" }}
    >
      <body
        className="flex flex-col bg-[#060608] text-white"
        style={{ minBlockSize: "100%" }}
      >
        <LocaleProvider>
          {children}
        </LocaleProvider>
      </body>
    </html>
  );
}
```
3. Remove or delete the unused `frontend/src/app/root-html.tsx` file (or keep it as an empty or inactive file if deletion is not preferred, but deleting or cleaning up is standard).
4. Run the Next.js production build (`npm run build` or `npx next build` inside the `frontend` folder) to verify that the build succeeds with 0 errors.
5. Run the python backend test suite (`pytest`) to confirm all 253 tests pass cleanly.
6. Create your agent metadata folder `.agents/worker_nextjs_build_fix_gen6` and write your `progress.md` and `handoff.md` there, recording the exact build commands, outputs, and diffs.
