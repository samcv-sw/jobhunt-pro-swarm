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
        dir="auto"
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
