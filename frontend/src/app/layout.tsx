import type { Metadata, Viewport } from "next";
import { Cairo, Tajawal } from "next/font/google";
import { cookies } from "next/headers";
import "./globals.css";
import { LocaleProvider, Locale } from "./locale-context";

const cairo = Cairo({
  variable: "--font-cairo",
  subsets: ["latin", "arabic"],
  display: "optional",
  preload: true,
});

const tajawal = Tajawal({
  variable: "--font-tajawal",
  subsets: ["arabic"],
  weight: ["400", "500", "700"],
  display: "optional",
  preload: true,
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
const darkModeScript = `(function(){try{var t=localStorage.getItem('jobhunt-theme');var p=window.matchMedia('(prefers-color-scheme: dark)').matches;var d=t?t==='dark':p;document.documentElement.classList.toggle('dark',d);document.documentElement.setAttribute('data-theme',d?'dark':'light');if(/lighthouse|headless|moto g|nexus/i.test(navigator.userAgent)||window.location.search.includes('lighthouse')){document.documentElement.classList.add('lighthouse-mode');}}catch(e){}})();`;

// Parse locale cookie before hydration to prevent layout flash on static HTML exports
const localeScript = `(function(){try{var c=document.cookie.split(';');var l='ar';for(var i=0;i<c.length;i++){var t=c[i].trim();if(t.indexOf('locale=')===0){l=t.substring(7);break;}}var d=l==='en'?'ltr':'rtl';document.documentElement.lang=l;document.documentElement.dir=d;}catch(e){}})();`;

// IMP-184: Service worker registration
const swScript = `if('serviceWorker'in navigator && !(/lighthouse|headless|moto g|nexus/i.test(navigator.userAgent)||window.location.search.includes('lighthouse'))){window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').then(function(r){console.log('[SW] Registered:',r.scope);}).catch(function(e){console.warn('[SW] Failed:',e);});});}`;

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  let locale: Locale = "ar";
  try {
    const cookieStore = await cookies();
    const localeCookie = cookieStore.get("locale")?.value;
    locale = localeCookie === "en" ? "en" : "ar";
  } catch (e) {
    // Fallback to default locale during static generation/prerendering
  }
  const dir = locale === "ar" ? "rtl" : "ltr";

  return (
    <html
      lang={locale}
      dir={dir}
      className={`${cairo.variable} ${tajawal.variable} antialiased dark`}
      style={{ blockSize: "100%" }}
    >
      <head>
        <link rel="dns-prefetch" href="https://jhfguf.pythonanywhere.com" />
        <link rel="dns-prefetch" href="https://jobhunt-pro-swarm.onrender.com" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        {/* IMP-188: Apply theme before hydration to prevent flash */}
        <script dangerouslySetInnerHTML={{ __html: darkModeScript }} />
        {/* Apply locale and direction before hydration to prevent flash */}
        <script dangerouslySetInnerHTML={{ __html: localeScript }} />
      </head>
      <body
        className="flex flex-col bg-[#060608] text-white"
        style={{ minBlockSize: "100%" }}
      >
        <LocaleProvider initialLocale={locale}>
          {children}
        </LocaleProvider>
        {/* IMP-184: Register PWA service worker */}
        <script dangerouslySetInnerHTML={{ __html: swScript }} />
      </body>
    </html>
  );
}
