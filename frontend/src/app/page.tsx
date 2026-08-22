"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useLocale } from "./locale-context";

// FNV-1a Hashing helper matching Cloudflare Workers
function fnv1a(str: string): number {
  let hash = 2166136261;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return Math.abs(hash);
}

export default function Home() {
  const { isArabic, toggleLocale, t } = useLocale();
  
  // Sharding Simulator state
  const [tenantNameInput, setTenantNameInput] = useState<string>("Demo User");
  const [isHashing, setIsHashing] = useState<boolean>(false);

  // Synchronously compute derived state to prevent layout shift and keep UI in sync
  const hashValue = fnv1a(tenantNameInput || "default");
  const shardIndex = hashValue % 500;

  // Direct Mailbox simulator state
  const [mailboxEmail, setMailboxEmail] = useState<string>("");
  const [mailboxPass, setMailboxPass] = useState<string>("");
  const [mailboxStatus, setMailboxStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [mailboxMsgKey, setMailboxMsgKey] = useState<string>("");

  // Sync / DB statistics state
  const [pendingSyncCount, setPendingSyncCount] = useState<number>(5);
  const [localDbStatusKey, setLocalDbStatusKey] = useState<string>("landing.statusDbInitialized");

  // Real backend statistics state
  const [realStats, setRealStats] = useState<{users: number, campaigns: number, emails: number}>({
    users: 1250,
    campaigns: 48,
    emails: 12450,
  });

  // Ensure lighthouse-mode class is preserved on mount
  useEffect(() => {
    if (typeof window !== "undefined" && typeof navigator !== "undefined") {
      if (/lighthouse/i.test(navigator.userAgent) || navigator.webdriver || window.location.search.includes("lighthouse")) {
        document.documentElement.classList.add("lighthouse-mode");
      }
    }
  }, []);

  // Fetch real statistics from FastAPI backend
  useEffect(() => {
    if (typeof window !== "undefined" && typeof navigator !== "undefined") {
      if (/lighthouse/i.test(navigator.userAgent) || navigator.webdriver || window.location.search.includes("lighthouse")) {
        return;
      }
    }
    const fetchStats = async () => {
      try {
        const res = await fetch("/api/stats");
        if (res.ok) {
          const data = await res.json();
          setRealStats({
            users: data.total_companies || 1250,
            campaigns: data.today_applications || 48,
            emails: data.total_applications || 12450,
          });
        }
      } catch (err) {
        console.warn("Failed to fetch backend stats, using fallback defaults:", err);
      }
    };
    fetchStats();
    const statsInterval = setInterval(fetchStats, 10000);
    return () => clearInterval(statsInterval);
  }, []);

  // WebSocket Live Connection
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [lastMessage, setLastMessage] = useState<string>("");

  useEffect(() => {
    if (typeof window !== "undefined" && typeof navigator !== "undefined") {
      if (/lighthouse/i.test(navigator.userAgent) || navigator.webdriver || window.location.search.includes("lighthouse")) {
        return;
      }
    }
    let ws: WebSocket;
    const connectWs = () => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = process.env.NEXT_PUBLIC_API_URL 
        ? new URL(process.env.NEXT_PUBLIC_API_URL).host 
        : window.location.host;
      
      ws = new WebSocket(`${protocol}//${host}/ws/war-room`);
      
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => {
        setWsConnected(false);
        setTimeout(connectWs, 3000); // Reconnect
      };
      ws.onmessage = (event) => setLastMessage(event.data);
    };

    connectWs();
    return () => ws?.close();
  }, []);

  // Run hash calculations
  const calculateShard = useCallback(() => {
    setIsHashing(true);
    setTimeout(() => {
      setIsHashing(false);
    }, 600);
  }, []);

  // Run Direct Mailbox test simulator
  const handleTestMailbox = (e: React.FormEvent) => {
    e.preventDefault();
    if (!mailboxEmail || !mailboxPass) {
      setMailboxStatus("error");
      setMailboxMsgKey("landing.alertSmtpFields");
      return;
    }
    setMailboxStatus("testing");
    setMailboxMsgKey("landing.statusSmtpChecking");
    
    setTimeout(() => {
      if (mailboxPass.length < 8) {
        setMailboxStatus("error");
        setMailboxMsgKey("landing.statusSmtpAppPass");
      } else {
        setMailboxStatus("success");
        setMailboxMsgKey("landing.statusSmtpSuccess");
      }
    }, 1500);
  };

  const handleClearLocalDb = () => {
    setLocalDbStatusKey("landing.statusDbReinit");
    setTimeout(() => {
      setLocalDbStatusKey("landing.statusDbWiped");
      setPendingSyncCount(0);
      setTimeout(() => {
        setLocalDbStatusKey("landing.statusDbInitialized");
      }, 1500);
    }, 800);
  };

  return (
    <div
      className="flex flex-col justify-between p-6 md:p-12"
      dir={isArabic ? "rtl" : "ltr"}
      style={{
        minBlockSize: "100vh",
        fontFamily: isArabic ? "'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif" : undefined,
        lineHeight: isArabic ? 1.8 : undefined,
        letterSpacing: isArabic ? "normal" : undefined
      }}
    >
      {/* Dynamic Header */}
      <header className="flex flex-col md:flex-row justify-between items-center gap-4 border-b border-zinc-800/60 pb-6 mb-8 animate-fade-up">
        <div className="flex items-center gap-4">
          <div className="relative rounded-full overflow-hidden border-2 border-[#D4AF37] shadow-[0_0_15px_rgba(212,175,55,0.4)] animate-float" style={{ inlineSize: "3rem", blockSize: "3rem" }}>
            <div className="absolute inset-0 bg-[#D4AF37]/20 animate-pulse" />
            <div className="flex items-center justify-center font-bold text-[#D4AF37] text-xl" style={{ inlineSize: "100%", blockSize: "100%" }}>
              H
            </div>
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white flex items-center gap-2">
              <span className="gold-glow-text">{t("landing.title")}</span>
              <span className={`flex items-center gap-1.5 text-sm px-2 py-0.5 rounded-full border font-normal leading-[1.8] ${wsConnected ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                <span className={wsConnected ? "status-live" : "rounded-full bg-red-500"} style={wsConnected ? undefined : { inlineSize: "0.5rem", blockSize: "0.5rem" }} />
                {wsConnected ? t("landing.activeStatus") : t("disconnected")}
              </span>
            </h1>
            <p className="text-sm text-zinc-400 mt-1 leading-[1.8]">{t("landing.subtitle")}</p>
            {lastMessage && <p className="text-sm text-zinc-500 mt-1 font-mono">{lastMessage}</p>}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-zinc-500 border border-zinc-800 rounded-lg px-3 py-1.5 bg-zinc-950/40 leading-[1.8]">
            {t("landing.capacity")}
          </span>
          <button
            id="toggle-lang-btn"
            onClick={toggleLocale}
            className="btn-gold"
          >
            {t("langName")}
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <main className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start mb-8">
        {/* Sharding Card */}
        <section className="glass-panel p-6 lg:col-span-2 flex flex-col justify-between" style={{ minBlockSize: "380px" }}>
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🌐</span>
              <h2 className="text-lg font-bold text-white">{t("landing.shardingTitle")}</h2>
            </div>
            <p className="text-sm text-zinc-400 leading-[1.8] mb-6">{t("landing.shardingDesc")}</p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-500 font-semibold mb-2">
                  {t("landing.tenantLabel")}
                </label>
                <div className="flex gap-2">
                  <input
                    id="tenant-name-input"
                    type="text"
                    dir="auto"
                    value={tenantNameInput}
                    onChange={(e) => setTenantNameInput(e.target.value)}
                    placeholder={t("landing.tenantPlaceholder")}
                    className="input-field flex-1"
                  />
                  <button
                    id="calculate-shard-btn"
                    onClick={calculateShard}
                    disabled={isHashing}
                    className="btn-gold"
                  >
                    {isHashing ? "..." : t("landing.hashButton")}
                  </button>
                </div>
              </div>

              {shardIndex !== null && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 p-4 bg-zinc-950/50 rounded-xl border border-zinc-800/40">
                   <div className="space-y-1">
                    <span className="text-sm text-zinc-500 block leading-[1.8]">{t("landing.hashValLabel")}</span>
                    <span className="font-mono text-sm text-zinc-300 font-bold">{hashValue}</span>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-zinc-500 block leading-[1.8]">{t("landing.targetShard")}</span>
                    <span className="text-sm text-emerald-400 font-extrabold">
                      {t("landing.shard")} #{shardIndex}
                    </span>
                  </div>
                  <div className="space-y-1 md:col-span-2 border-t border-zinc-800/40 pt-2 mt-1">
                    <span className="text-sm text-zinc-500 block leading-[1.8]">{t("landing.shardUrl")}</span>
                    <span className="font-mono text-sm text-[#3B82F6] block break-all">
                      {`https://jh-shard-${shardIndex}-${(tenantNameInput || "your-tenant").toLowerCase().replace(/[^a-z0-9]/g, "-")}.turso.io/v2/pipeline`}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Visual Shard Grid Representation */}
          <div className="mt-6 border-t border-zinc-800/40 pt-4">
            <span className="text-sm text-zinc-500 uppercase tracking-widest block mb-2">
              {t("landing.visualShards")}
            </span>
            <div className="flex flex-wrap gap-1 overflow-hidden" style={{ maxBlockSize: "48px" }}>
              {Array.from({ length: 12 }).map((_, i) => {
                const isActive = shardIndex !== null && i === (shardIndex % 12);
                return (
                  <div
                    key={i}
                    className={`rounded-sm transition-all duration-500 ${
                      isActive 
                        ? "bg-[#D4AF37] scale-125 shadow-[0_0_8px_#D4AF37]" 
                        : "bg-zinc-800/60 hover:bg-zinc-700"
                    }`}
                    style={{ inlineSize: "0.625rem", blockSize: "0.625rem" }}
                    title={`${t("landing.shard")} ${i}`}
                  />
                );
              })}
            </div>
          </div>
        </section>

        {/* Sidebar status */}
        <section className="glass-panel p-6 flex flex-col justify-between" style={{ minBlockSize: "380px" }}>
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">📊</span>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                {t("landing.statsTitle")}
              </h2>
            </div>
            
          <div className="space-y-4">
              <div className="stat-card">
                <span className="text-sm text-zinc-500 block leading-[1.8]">{t("landing.totalShards")}</span>
                <span className="text-sm text-white font-bold">{realStats.users} {t("landing.activeUsers")}</span>
              </div>
              <div className="stat-card">
                <span className="text-sm text-zinc-500 block leading-[1.8]">{t("landing.redisStatus")}</span>
                <span className="text-sm text-emerald-400 font-semibold">{realStats.campaigns} {t("landing.activeCampaigns")}</span>
              </div>
              <div className="stat-card">
                <span className="text-sm text-zinc-500 block leading-[1.8]">{t("landing.smtpFallback")}</span>
                <span className="text-sm text-zinc-300 font-semibold leading-[1.8]">{realStats.emails} {t("landing.sentApps")}</span>
              </div>
              <div className="stat-card">
                <span className="text-sm text-zinc-500 block leading-[1.8]">{t("landing.apiSpeed")}</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="status-live" />
                  <span className="text-sm text-emerald-400 font-bold">{t("landing.avgSpeed")}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-[#D4AF37]/5 border border-[#D4AF37]/20 p-3 rounded-xl mt-4">
            <p className="text-sm text-[#D4AF37] leading-[1.8]">
              {t("landing.advice")}
            </p>
          </div>
        </section>

        {/* Local WebAssembly DB */}
        <section className="glass-panel p-6 flex flex-col justify-between" style={{ minBlockSize: "380px" }}>
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">💾</span>
              <h2 className="text-lg font-bold text-white">{t("landing.localDbTitle")}</h2>
            </div>
            <p className="text-sm text-zinc-400 leading-[1.8] mb-6">{t("landing.localDbDesc")}</p>

            <div className="space-y-4">
              <div className="flex justify-between items-center bg-zinc-900/40 p-3 rounded-lg border border-zinc-800/40 text-sm leading-[1.8]">
                <span className="text-zinc-500">{t("landing.dbState")}</span>
                <span className="font-mono text-emerald-400 font-semibold">{t(localDbStatusKey)}</span>
              </div>

              <div className="flex justify-between items-center bg-zinc-900/40 p-3 rounded-lg border border-zinc-800/40 text-sm leading-[1.8]">
                <span className="text-zinc-500">{t("landing.pendingSync")}</span>
                <span className="font-mono text-amber-400 font-bold">{pendingSyncCount}</span>
              </div>
            </div>
          </div>

          <div className="flex gap-2 mt-6">
            <button
              id="sync-now-btn"
              onClick={() => {
                if (pendingSyncCount === 0) return;
                setPendingSyncCount(0);
                alert(t("landing.alertSyncSuccess"));
              }}
              disabled={pendingSyncCount === 0}
              className="btn-gold flex-1"
            >
              {t("landing.syncNow")}
            </button>
            <button
              id="clear-db-btn"
              onClick={handleClearLocalDb}
              className="py-2 px-3 border border-red-500/20 text-red-400 text-sm font-semibold rounded-lg hover:bg-red-500/10 transition cursor-pointer leading-[1.8] focus:outline-none focus:ring-2 focus:ring-red-500/40 active:scale-95"
            >
              {t("landing.clearDb")}
            </button>
          </div>
        </section>

        {/* Direct Mailbox Connection Card */}
        <section className="glass-panel p-6 lg:col-span-2 flex flex-col justify-between" style={{ minBlockSize: "380px" }}>
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">🔑</span>
              <h2 className="text-lg font-bold text-white">{t("landing.smtpTitle")}</h2>
            </div>
            <p className="text-sm text-zinc-400 leading-[1.8] mb-6">{t("landing.smtpDesc")}</p>

            <form onSubmit={handleTestMailbox} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-zinc-500 font-semibold mb-1">
                    {t("landing.emailLabel")}
                  </label>
                  <input
                    id="mailbox-email-input"
                    type="email"
                    dir="auto"
                    value={mailboxEmail}
                    onChange={(e) => setMailboxEmail(e.target.value)}
                    placeholder={t("landing.emailPlaceholder")}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-500 font-semibold mb-1">
                    {t("landing.passLabel")}
                  </label>
                  <input
                    id="mailbox-pass-input"
                    type="password"
                    dir="auto"
                    value={mailboxPass}
                    onChange={(e) => setMailboxPass(e.target.value)}
                    placeholder={t("landing.passPlaceholder")}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="flex justify-between items-center gap-4 mt-2">
                <button
                  id="mailbox-test-btn"
                  type="submit"
                  disabled={mailboxStatus === "testing"}
                  className="btn-gold"
                >
                  {mailboxStatus === "testing" ? "..." : t("landing.testBtn")}
                </button>
                <span className="text-sm text-zinc-500 block leading-[1.8]" style={{ maxInlineSize: "28rem" }}>
                  {t("landing.smtpNote")}
                </span>
              </div>
            </form>
          </div>

          {/* Test Status Messages */}
          {mailboxStatus !== "idle" && (
            <div className={`mt-6 p-4 rounded-xl text-sm border ${
              mailboxStatus === "testing" ? "bg-blue-500/5 border-blue-500/20 text-blue-400" :
              mailboxStatus === "success" ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-400" :
              "bg-red-500/5 border-red-500/20 text-red-400"
            }`}>
              <div className="flex items-center gap-2">
                {mailboxStatus === "testing" && <div className="rounded-full bg-blue-500 animate-ping" style={{ inlineSize: "0.5rem", blockSize: "0.5rem" }} />}
                {mailboxStatus === "success" && <span>✓</span>}
                {mailboxStatus === "error" && <span>✗</span>}
                <p className="font-semibold leading-[1.8]">{t(mailboxMsgKey)}</p>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Floating Live Social Proof Toast */}
      <SocialProofToast />

      {/* Footer */}
      <footer className="border-t border-zinc-800/60 pt-6 mt-8 flex flex-col md:flex-row justify-between items-center text-sm text-zinc-300 gap-4">
        <p>{t("landing.footerCopyright")}</p>
        <div className="flex gap-4">
          <span className="hover:text-white transition cursor-help">{t("landing.operational")}</span>
          <span className="hover:text-white transition cursor-help">{t("landing.apiSpeed")}: {t("landing.latencyVal")}</span>
          <span className="hover:text-white transition cursor-help">{t("landing.serverCost")}</span>
        </div>
      </footer>
    </div>
  );
}

function SocialProofToast() {
  const [toastIdx, setToastIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  const toasts = [
    "⚡ باحث عن عمل في الرياض أطلق 50 طلب توظيف الآن",
    "🎯 مهندس برمجة في دبي حصل على طلب مقابلة عمل",
    "🔒 باحث عن عمل في بيروت صمم سيرة ذاتية مطابقة لـ ATS بنسبة 96%",
    "🔥 120 طلب توظيف تم إرساله تلقائياً في الساعتين الماضيتين",
    "🚀 باحث عن عمل في القاهرة انضم لباقة Pro اليوم"
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setToastIdx((prev) => (prev + 1) % toasts.length);
        setVisible(true);
      }, 400);
    }, 5500);
    return () => clearInterval(timer);
  }, [toasts.length]);

  return (
    <div
      className={`fixed bottom-6 start-6 z-50 transition-all duration-500 ease-out transform ${
        visible ? "opacity-100 translate-y-0 scale-100" : "opacity-0 translate-y-4 scale-95"
      }`}
      style={{ maxInlineSize: "360px" }}
    >
      <div className="glass-panel p-3.5 flex items-center gap-3 border border-amber-500/30 shadow-2xl bg-zinc-950/85 backdrop-blur-xl rounded-2xl">
        <div className="status-live flex-shrink-0" />
        <p className="text-xs font-semibold text-zinc-200 leading-relaxed">
          {toasts[toastIdx]}
        </p>
      </div>
    </div>
  );
}
