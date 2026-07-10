"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { runLocalQuery } from "../db/wasm-db";
import { useLocale } from "../locale-context";

interface ScrapeRecord {
  id: number;
  company_name: string;
  job_title: string;
  source: string;
  status: "completed" | "processing" | "failed";
  scraped_at: string;
}

// Robust fallback mock data for testing and initial rendering
const MOCK_SCRAPES: ScrapeRecord[] = [
  {
    id: 1,
    company_name: "Aramco / أرامكو",
    job_title: "Senior AI Engineer / مهندس ذكاء اصطناعي أول",
    source: "LinkedIn",
    status: "completed",
    scraped_at: "2026-07-03 12:45",
  },
  {
    id: 2,
    company_name: "NEOM / نيوم",
    job_title: "Full Stack Developer / مطور ويب متكامل",
    source: "Indeed",
    status: "processing",
    scraped_at: "2026-07-03 12:15",
  },
  {
    id: 3,
    company_name: "SDAIA / سدايا",
    job_title: "Data Scientist / عالم بيانات",
    source: "GulfTalent",
    status: "completed",
    scraped_at: "2026-07-03 11:30",
  },
  {
    id: 4,
    company_name: "Solutions by stc",
    job_title: "DevOps Engineer / مهندس عمليات تطوير",
    source: "LinkedIn",
    status: "failed",
    scraped_at: "2026-07-03 10:05",
  },
  {
    id: 5,
    company_name: "Emirates Group / طيران الإمارات",
    job_title: "Cloud Architect / خبير بنية سحابية",
    source: "LinkedIn",
    status: "completed",
    scraped_at: "2026-07-02 18:20",
  },
  {
    id: 6,
    company_name: "e& UAE / اتصالات",
    job_title: "Cybersecurity Specialist / أخصائي أمن سيبراني",
    source: "Indeed",
    status: "completed",
    scraped_at: "2026-07-02 15:40",
  },
];

export default function Dashboard() {
  const { isArabic, toggleLocale } = useLocale();
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [scrapes, setScrapes] = useState<ScrapeRecord[]>([]);
  const [dbLoading, setDbLoading] = useState<boolean>(true);
  const [randomMetric] = useState<number>(() => Math.floor(Math.random() * 4) + 1);

  // Live Statistics state
  const [stats, setStats] = useState({
    totalScrapes: 1245,
    successRate: 94.2,
    activeScrapers: 8,
    systemLoad: 12.4,
  });

  // Load from Browser WebAssembly SQLite DB if available
  useEffect(() => {
    async function loadData() {
      try {
        // Query campaigns to count total and success rate
        const campaignsQuery = await runLocalQuery("SELECT * FROM local_campaigns;");
        
        let dbTotal = 0;
        let dbSent = 0;
        
        if (campaignsQuery && campaignsQuery.length > 0) {
          const values = campaignsQuery[0].values;
          // campaigns table cols: id, campaign_id, status, total_companies, sent_count, created_at
          values.forEach(row => {
            dbTotal += Number(row[3]) || 0; // total_companies
            dbSent += Number(row[4]) || 0;  // sent_count
          });
        }

        // Query local_scrapes if table exists (dynamic scheme check)
        const scrapesQuery = await runLocalQuery(
          "SELECT * FROM local_scrapes ORDER BY scraped_at DESC LIMIT 20;"
        ).catch(() => null);

        if (scrapesQuery && scrapesQuery.length > 0) {
          const cols = scrapesQuery[0].columns;
          const vals = scrapesQuery[0].values;
          const formatted = vals.map(row => {
            const obj: Record<string, unknown> = {};
            cols.forEach((col, idx) => {
              obj[col] = row[idx];
            });
            return obj as unknown as ScrapeRecord;
          });
          setScrapes(formatted);
        } else {
          setScrapes(MOCK_SCRAPES);
        }

        // Dynamically update stats if we found database records
        if (dbTotal > 0) {
          setStats(prev => ({
            ...prev,
            totalScrapes: dbTotal,
            successRate: dbTotal > 0 ? parseFloat(((dbSent / dbTotal) * 100).toFixed(1)) : 94.2,
          }));
        }
      } catch (err) {
        console.warn("[Dashboard-DB] Wasm DB fallback enabled (using mock datasets):", err);
        setScrapes(MOCK_SCRAPES);
      } finally {
        setDbLoading(false);
      }
    }

    loadData();

    // Live Web Scraper simulation (updates statistics slightly over time)
    const interval = setInterval(() => {
      setStats(prev => {
        const delta = Math.random() > 0.4 ? 1 : 0;
        const newTotal = prev.totalScrapes + delta;
        const newLoad = Math.max(5, Math.min(95, parseFloat((prev.systemLoad + (Math.random() * 4 - 2)).toFixed(1))));
        return {
          ...prev,
          totalScrapes: newTotal,
          systemLoad: newLoad,
        };
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Filter scrapes based on search input
  const filteredScrapes = scrapes.filter(
    item =>
      item.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.job_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.source.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Translation mapping
  const t = {
    title: isArabic ? "لوحة التحكم الذكية" : "AI Automation Dashboard",
    subtitle: isArabic
      ? "مراقبة وإدارة حملات التقديم واستخراج الوظائف الذكية"
      : "Monitor & manage application campaigns and smart job extraction",
    backHome: isArabic ? "العودة للرئيسية" : "Back to Home",
    liveStats: isArabic ? "الإحصاءات الحية" : "Live Statistics",

    // Stats Labels
    totalScrapes: isArabic ? "إجمالي الوظائف المسحوبة" : "Total Scrapes",
    successRate: isArabic ? "معدل نجاح التقديم" : "Success Rate",
    activeScrapers: isArabic ? "المستخرجات النشطة" : "Active Scrapers",
    systemLoad: isArabic ? "ضغط النظام" : "System Load",

    // Status Values
    running: isArabic ? "يعمل الآن" : "Running",
    idle: isArabic ? "خامل" : "Idle",
    healthy: isArabic ? "مستقر" : "Healthy",
    optimal: isArabic ? "مثالي" : "Optimal",

    // Table labels
    historyTitle: isArabic ? "سجل عمليات السحب والتقديم" : "Historical Scrapes & Applications",
    historyDesc: isArabic
      ? "قائمة تفصيلية بآخر الوظائف التي تم سحبها وحالة التقديم عليها"
      : "Detailed list of recent scraped jobs and their application status",
    searchPlaceholder: isArabic ? "ابحث عن شركة، مسمى وظيفي أو مصدر..." : "Search company, job title or source...",
    colDate: isArabic ? "التاريخ والوقت" : "Date & Time",
    colCompany: isArabic ? "الشركة" : "Company",
    colJob: isArabic ? "المسمى الوظيفي" : "Job Title",
    colSource: isArabic ? "المصدر" : "Source",
    colStatus: isArabic ? "الحالة" : "Status",
    colActions: isArabic ? "الإجراءات" : "Actions",

    statusCompleted: isArabic ? "مكتمل" : "Completed",
    statusProcessing: isArabic ? "جاري المعالجة" : "Processing",
    statusFailed: isArabic ? "فشل" : "Failed",

    btnRetry: isArabic ? "إعادة المحاولة" : "Retry",
    btnView: isArabic ? "عرض التفاصيل" : "View Details",

    // Analytics Section
    analyticsTitle: isArabic ? "التحليل البياني الأسبوعي" : "Weekly Performance Analytics",
    analyticsDesc: isArabic
      ? "مقارنة حجم سحب الوظائف ومعدل القبول الأسبوعي"
      : "Weekly job scraping volume vs acceptance rate comparison",
    chartScrapes: isArabic ? "الوظائف المسحوبة" : "Scraped Jobs",
    chartApplications: isArabic ? "الطلبات المرسلة" : "Submitted Apps",

    // Footer
    footerText: isArabic
      ? "💡 تعمل البنية التحتية بالكامل على خوادم الحافة بتكلفة صفرية مطلقة."
      : "💡 Infrastructure is fully deployed at Cloud Edge with zero operational overhead.",
    copyright: isArabic
      ? "© 2026 JobHunt Pro. تم التطوير بحب في لبنان. محرك هيدرا اللامركزي نشط."
      : "© 2026 JobHunt Pro. Built with love in Lebanon. Decentralized sovereign engine active.",
  };

  // Mock Weekly Chart Data
  const chartDays = isArabic
    ? ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
    : ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"];
  const chartScrapeValues = [65, 84, 92, 71, 110, 125, 95];
  const chartAppValues = [60, 78, 88, 64, 105, 120, 90];

  return (
    <div
      dir={isArabic ? "rtl" : "ltr"}
      className="flex flex-col justify-between p-6 md:p-12 bg-[#060608] text-[#f4f4f7] selection:bg-[#D4AF37]/30"
      style={{ minBlockSize: "100vh", fontFamily: "var(--font-arabic)" }}
    >
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-center gap-4 border-b border-zinc-800/60 pb-6 mb-8 animate-fade-up">
        <div className="flex items-center gap-4">
          <div className="relative rounded-full overflow-hidden border-2 border-[#D4AF37] shadow-[0_0_15px_rgba(212,175,55,0.4)] animate-float" style={{ inlineSize: "3rem", blockSize: "3rem" }}>
            <div className="absolute inset-0 bg-[#D4AF37]/20 animate-pulse" />
            <div className="flex items-center justify-center font-bold text-[#D4AF37] text-xl" style={{ inlineSize: "100%", blockSize: "100%" }}>
              H
            </div>
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-normal text-white flex items-center gap-2">
              <span className="gold-glow-text">{t.title}</span>
              <span className="flex items-center gap-1.5 text-sm px-2.5 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 font-normal">
                <span className="status-live" />
                {t.healthy}
              </span>
            </h1>
            <p className="text-sm text-zinc-400 mt-1">{t.subtitle}</p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="text-sm text-zinc-400 hover:text-white border border-zinc-800 rounded-lg px-4 py-2 bg-zinc-950/40 transition hover:bg-zinc-900/60"
          >
            <span className="dir-icon inline-block me-1 font-semibold">
              {isArabic ? "←" : "←"}
            </span>
            {t.backHome}
          </Link>
          <button
            onClick={toggleLocale}
            className="btn-gold"
          >
            {isArabic ? "English" : "العربية (RTL)"}
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        
        {/* Row 1: Live Statistics (4 cards in grid) */}
        <section className="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 animate-fade-up">
          
          {/* Stat 1: Total Scrapes */}
          <div className="glass-panel p-6 flex flex-col justify-between" style={{ minBlockSize: "140px" }}>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-zinc-400">{t.totalScrapes}</span>
                <span className="text-2xl">🕸️</span>
              </div>
              <p className="text-3xl font-bold text-white mt-1">
                {stats.totalScrapes.toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-1.5 mt-4 text-sm text-emerald-400">
              <span className="font-mono">+{randomMetric}</span>
              <span>{isArabic ? "منذ دقيقة" : "new metrics / min"}</span>
            </div>
          </div>

          {/* Stat 2: Success Rate */}
          <div className="glass-panel p-6 flex flex-col justify-between" style={{ minBlockSize: "140px" }}>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-zinc-400">{t.successRate}</span>
                <span className="text-2xl text-emerald-400">📈</span>
              </div>
              <p className="text-3xl font-bold text-white mt-1">
                {stats.successRate}%
              </p>
            </div>
            <div className="flex items-center gap-1.5 mt-4 text-sm text-emerald-400">
              <span className="status-live" />
              <span>{t.optimal}</span>
            </div>
          </div>

          {/* Stat 3: Active Scrapers */}
          <div className="glass-panel p-6 flex flex-col justify-between" style={{ minBlockSize: "140px" }}>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-zinc-400">{t.activeScrapers}</span>
                <span className="text-2xl">🤖</span>
              </div>
              <p className="text-3xl font-bold text-white mt-1">
                {stats.activeScrapers}
              </p>
            </div>
            <div className="flex items-center gap-1.5 mt-4 text-sm text-[#3B82F6]">
              <div className="rounded-full bg-[#3B82F6] animate-ping" style={{ inlineSize: "0.625rem", blockSize: "0.625rem" }} />
              <span>{t.running}</span>
            </div>
          </div>

          {/* Stat 4: System Load */}
          <div className="glass-panel p-6 flex flex-col justify-between" style={{ minBlockSize: "140px" }}>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-zinc-400">{t.systemLoad}</span>
                <span className="text-2xl">⚡</span>
              </div>
              <p className="text-3xl font-bold text-white mt-1">
                {stats.systemLoad}%
              </p>
            </div>
            <div className="flex items-center gap-1.5 mt-4 text-sm text-[#D4AF37]">
              <span>{isArabic ? "استهلاك الحافة" : "Edge Computing Usage"}</span>
            </div>
          </div>

        </section>

        {/* Row 2: Left: Historical Table (col-span-2) | Right: Analytics Card (col-span-1) */}
        
        {/* Historical Scrapes Table */}
        <section className="glass-panel p-6 lg:col-span-2 flex flex-col justify-between animate-fade-up stagger-1" style={{ minBlockSize: "500px" }}>
          <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
              <div>
                <h2 className="text-lg font-bold text-white">{t.historyTitle}</h2>
                <p className="text-sm text-zinc-400 mt-1">{t.historyDesc}</p>
              </div>

              {/* Table Search Input */}
              <div className="relative" style={{ inlineSize: "100%", maxInlineSize: "280px" }}>
                <input
                  type="text"
                  dir="auto"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder={t.searchPlaceholder}
                  className="input-field py-2"
                />
              </div>
            </div>

            {/* Responsive Table Container */}
            <div className="overflow-x-auto">
              <table className="text-start border-collapse text-sm" style={{ inlineSize: "100%" }}>
                <thead>
                  <tr className="border-b border-zinc-800/80 text-zinc-400">
                    <th className="py-3 px-4 text-start font-semibold">{t.colDate}</th>
                    <th className="py-3 px-4 text-start font-semibold">{t.colCompany}</th>
                    <th className="py-3 px-4 text-start font-semibold">{t.colJob}</th>
                    <th className="py-3 px-4 text-start font-semibold">{t.colSource}</th>
                    <th className="py-3 px-4 text-start font-semibold">{t.colStatus}</th>
                    <th className="py-3 px-4 text-start font-semibold">{t.colActions}</th>
                  </tr>
                </thead>
                <tbody>
                  {dbLoading ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-zinc-500 font-medium">
                        {isArabic ? "جاري تحميل السجلات المحلية..." : "Loading local records..."}
                      </td>
                    </tr>
                  ) : filteredScrapes.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-zinc-500 font-medium">
                        {isArabic ? "لا توجد سجلات مطابقة للبحث." : "No records matching search."}
                      </td>
                    </tr>
                  ) : (
                    filteredScrapes.map((row) => (
                      <tr key={row.id} className="border-b border-zinc-900/60 hover:bg-zinc-900/30 transition-colors">
                        <td className="py-3.5 px-4 font-mono text-zinc-300 whitespace-nowrap">{row.scraped_at}</td>
                        <td className="py-3.5 px-4 font-bold text-white whitespace-nowrap">{row.company_name}</td>
                        <td className="py-3.5 px-4 text-zinc-300">{row.job_title}</td>
                        <td className="py-3.5 px-4 text-zinc-400 whitespace-nowrap">{row.source}</td>
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          {row.status === "completed" && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 font-medium">
                              <span className="rounded-full bg-emerald-400" style={{ inlineSize: "0.375rem", blockSize: "0.375rem" }} />
                              {t.statusCompleted}
                            </span>
                          )}
                          {row.status === "processing" && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/5 text-blue-400 font-medium">
                              <span className="rounded-full bg-blue-400 animate-pulse" style={{ inlineSize: "0.375rem", blockSize: "0.375rem" }} />
                              {t.statusProcessing}
                            </span>
                          )}
                          {row.status === "failed" && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border border-red-500/20 bg-red-500/5 text-red-400 font-medium">
                              <span className="rounded-full bg-red-400" style={{ inlineSize: "0.375rem", blockSize: "0.375rem" }} />
                              {t.statusFailed}
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          {row.status === "failed" ? (
                            <button
                              onClick={() => alert(`Retrying job scrape id: ${row.id}`)}
                              className="text-sm font-bold text-[#D4AF37] hover:underline cursor-pointer"
                            >
                              {t.btnRetry}
                            </button>
                          ) : (
                            <button
                              onClick={() => alert(`Details for job id: ${row.id}`)}
                              className="text-sm font-bold text-zinc-400 hover:text-white hover:underline cursor-pointer"
                            >
                              {t.btnView}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Table Footer Stats */}
          <div className="flex justify-between items-center border-t border-zinc-900 pt-4 mt-6 text-sm text-zinc-500">
            <span>
              {isArabic
                ? `عرض ${filteredScrapes.length} من أصل ${scrapes.length} وظيفة`
                : `Showing ${filteredScrapes.length} of ${scrapes.length} entries`}
            </span>
            <span className="font-mono text-sm">SQLite WASM OPFS Storage</span>
          </div>
        </section>

        {/* Analytics Card */}
        <section className="glass-panel p-6 flex flex-col justify-between animate-fade-up stagger-2" style={{ minBlockSize: "500px" }}>
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">📊</span>
              <h2 className="text-lg font-bold text-white">{t.analyticsTitle}</h2>
            </div>
            <p className="text-sm text-zinc-400 leading-[1.8] mb-6">{t.analyticsDesc}</p>

            {/* Glassmorphic SVG Chart container */}
            <div className="p-4 bg-zinc-950/40 border border-zinc-900 rounded-xl">
              <svg viewBox="0 0 500 240" className="overflow-visible" style={{ inlineSize: "100%", blockSize: "auto" }}>
              {/* Horizontal grid lines */}
              <line x1="40" y1="40" x2="480" y2="40" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
              <line x1="40" y1="90" x2="480" y2="90" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
              <line x1="40" y1="140" x2="480" y2="140" stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
              <line x1="40" y1="190" x2="480" y2="190" stroke="rgba(255,255,255,0.1)" />

              {/* Y-axis Labels */}
                <text x="30" y="44" textAnchor="end" fill="#71717a" className="text-[14px] font-mono">150</text>
                <text x="30" y="94" textAnchor="end" fill="#71717a" className="text-[14px] font-mono">100</text>
                <text x="30" y="144" textAnchor="end" fill="#71717a" className="text-[14px] font-mono">50</text>
                <text x="30" y="194" textAnchor="end" fill="#71717a" className="text-[14px] font-mono">0</text>

                {/* Chart Area Gradient */}
                <defs>
                  <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#D4AF37" stopOpacity="0" />
                  </linearGradient>
                  <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {/* Draw Areas */}
                {/* Gold: Scrapes */}
                <path
                  d={`M 60,${190 - (chartScrapeValues[0] * 1)} 
                      L 125,${190 - (chartScrapeValues[1] * 1)} 
                      L 190,${190 - (chartScrapeValues[2] * 1)} 
                      L 255,${190 - (chartScrapeValues[3] * 1)} 
                      L 320,${190 - (chartScrapeValues[4] * 1)} 
                      L 385,${190 - (chartScrapeValues[5] * 1)} 
                      L 450,${190 - (chartScrapeValues[6] * 1)} 
                      L 450,190 L 60,190 Z`}
                  fill="url(#goldGradient)"
                />
                
                {/* Blue: Applications */}
                <path
                  d={`M 60,${190 - (chartAppValues[0] * 1)} 
                      L 125,${190 - (chartAppValues[1] * 1)} 
                      L 190,${190 - (chartAppValues[2] * 1)} 
                      L 255,${190 - (chartAppValues[3] * 1)} 
                      L 320,${190 - (chartAppValues[4] * 1)} 
                      L 385,${190 - (chartAppValues[5] * 1)} 
                      L 450,${190 - (chartAppValues[6] * 1)} 
                      L 450,190 L 60,190 Z`}
                  fill="url(#blueGradient)"
                />

                {/* Line Paths */}
                <path
                  d={`M 60,${190 - (chartScrapeValues[0] * 1)} 
                      L 125,${190 - (chartScrapeValues[1] * 1)} 
                      L 190,${190 - (chartScrapeValues[2] * 1)} 
                      L 255,${190 - (chartScrapeValues[3] * 1)} 
                      L 320,${190 - (chartScrapeValues[4] * 1)} 
                      L 385,${190 - (chartScrapeValues[5] * 1)} 
                      L 450,${190 - (chartScrapeValues[6] * 1)}`}
                  fill="none"
                  stroke="#D4AF37"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                <path
                  d={`M 60,${190 - (chartAppValues[0] * 1)} 
                      L 125,${190 - (chartAppValues[1] * 1)} 
                      L 190,${190 - (chartAppValues[2] * 1)} 
                      L 255,${190 - (chartAppValues[3] * 1)} 
                      L 320,${190 - (chartAppValues[4] * 1)} 
                      L 385,${190 - (chartAppValues[5] * 1)} 
                      L 450,${190 - (chartAppValues[6] * 1)}`}
                  fill="none"
                  stroke="#3B82F6"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeDasharray="3 3"
                />

                {/* Data Points */}
                {chartScrapeValues.map((val, idx) => (
                  <circle
                    key={`sc-${idx}`}
                    cx={60 + idx * 65}
                    cy={190 - val * 1}
                    r="4"
                    fill="#D4AF37"
                    stroke="#060608"
                    strokeWidth="1.5"
                  />
                ))}

                {/* X-axis Labels */}
                {chartDays.map((day, idx) => (
                  <text
                    key={`day-${idx}`}
                    x={60 + idx * 65}
                    y="215"
                    textAnchor="middle"
                    fill="#71717a"
                    className="text-[14px]"
                  >
                    {day}
                  </text>
                ))}
              </svg>
            </div>

            {/* Legend */}
            <div className="flex gap-4 justify-center mt-4">
              <div className="flex items-center gap-1.5 text-sm">
                <span className="inline-block bg-[#D4AF37] rounded-full" style={{ inlineSize: "0.875rem", blockSize: "0.25rem" }} />
                <span className="text-zinc-400">{t.chartScrapes}</span>
              </div>
              <div className="flex items-center gap-1.5 text-sm">
                <span className="inline-block border-t border-dashed border-[#3B82F6]" style={{ inlineSize: "0.875rem", blockSize: "0.25rem" }} />
                <span className="text-zinc-400">{t.chartApplications}</span>
              </div>
            </div>
          </div>

          {/* Quick AI Advice Box */}
          <div className="bg-[#D4AF37]/5 border border-[#D4AF37]/20 p-4 rounded-xl mt-6">
            <h3 className="text-sm font-bold text-[#D4AF37] mb-1">
              {isArabic ? "💡 نصيحة المساعد الذكي" : "💡 AI Recommendation"}
            </h3>
            <p className="text-sm text-zinc-300 leading-[1.8]">
              {isArabic
                ? "معدل النجاح مستقر عند 94%. ننصح بالتركيز على سحب الوظائف من LinkedIn خلال الساعات القادمة لتوفر عروض ممتازة مطابقة لملفك."
                : "Application success is optimal at 94%. We suggest scaling LinkedIn scraping volume in the next 12 hours based on profile matches."}
            </p>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/60 pt-6 mt-8 flex flex-col md:flex-row justify-between items-center text-sm text-zinc-500 gap-4">
        <p className="text-center md:text-start">{t.copyright}</p>
        <p className="text-zinc-400 text-center md:text-end">{t.footerText}</p>
      </footer>
    </div>
  );
}
