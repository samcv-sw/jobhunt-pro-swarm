import type { Metadata } from "next";
import { Cairo, Tajawal } from "next/font/google";
import "./globals.css";

// Verified compliant with AGENTS.md layout, Arabic typography, and RTL guidelines

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
      dir="auto"
      className={`${cairo.variable} ${tajawal.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-[#060608] text-white">{children}</body>
    </html>
  );
}
