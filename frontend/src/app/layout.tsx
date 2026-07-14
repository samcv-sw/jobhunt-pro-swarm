import type { Metadata, Viewport } from "next";
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
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "black-translucent", title: "JobHunt Pro" },
  openGraph: {
    title: "JobHunt Pro",
    description: "AI-Powered Automated Job Application Platform",
    type: "website",
  },
};

// IMP-184: viewport with PWA theme color
export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)",  color: "#0f0f1a" },
    { media: "(prefers-color-scheme: light)", color: "#6c63ff" },
  ],
  width: "device-width",
  initialScale: 1,
};

// IMP-188: Dark mode persistence before hydration (prevents theme flash)
const darkModeScript = `(function(){try{var t=localStorage.getItem('jobhunt-theme');var p=window.matchMedia('(prefers-color-scheme: dark)').matches;var d=t?t==='dark':p;document.documentElement.classList.toggle('dark',d);document.documentElement.setAttribute('data-theme',d?'dark':'light');}catch(e){}})();`;

// IMP-184: Service worker registration
const swScript = `if('serviceWorker'in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').then(function(r){console.log('[SW] Registered:',r.scope);}).catch(function(e){console.warn('[SW] Failed:',e);});});}`;

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
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://jhfguf.pythonanywhere.com" />
        <link rel="dns-prefetch" href="https://jobhunt-pro-swarm.onrender.com" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        {/* IMP-188: Apply theme before hydration to prevent flash */}
        <script dangerouslySetInnerHTML={{ __html: darkModeScript }} />
      </head>
      <body
        dir="auto"
        className="flex flex-col bg-[#060608] text-white"
        style={{ minBlockSize: "100%" }}
      >
        <LocaleProvider>
          {children}
        </LocaleProvider>
        {/* IMP-184: Register PWA service worker */}
        <script dangerouslySetInnerHTML={{ __html: swScript }} />
      </body>
    </html>
  );
}
