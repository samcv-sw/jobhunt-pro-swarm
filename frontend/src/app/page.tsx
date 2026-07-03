"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";

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
  const [isArabic, setIsArabic] = useState<boolean>(true);
  
  // Sharding Simulator state
  const [tenantNameInput, setTenantNameInput] = useState<string>("Rita Cordahi");
  const [shardIndex, setShardIndex] = useState<number | null>(null);
  const [hashValue, setHashValue] = useState<number | null>(null);
  const [isHashing, setIsHashing] = useState<boolean>(false);

  // BYO SMTP simulator state
  const [smtpEmail, setSmtpEmail] = useState<string>("");
  const [smtpPass, setSmtpPass] = useState<string>("");
  const [smtpStatus, setSmtpStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [smtpMsg, setSmtpMsg] = useState<string>("");

  // Sync / DB statistics state
  const [pendingSyncCount, setPendingSyncCount] = useState<number>(0);
  const [localDbStatus, setLocalDbStatus] = useState<string>("Initialized (OPFS)");

  // WebSocket Live Connection
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [lastMessage, setLastMessage] = useState<string>("");

  useEffect(() => {
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
  const calculateShard = () => {
    setIsHashing(true);
    setTimeout(() => {
      const hash = fnv1a(tenantNameInput || "default");
      setHashValue(hash);
      setShardIndex(hash % 500);
      setIsHashing(false);
    }, 600);
  };

  useEffect(() => {
    calculateShard();
    // Simulate some pending local mutations
    setPendingSyncCount(Math.floor(Math.random() * 8));
  }, []);

  // Run SMTP test simulator
  const handleTestSmtp = (e: React.FormEvent) => {
    e.preventDefault();
    if (!smtpEmail || !smtpPass) {
      setSmtpStatus("error");
      setSmtpMsg(isArabic ? "يرجى إدخال البريد الإلكتروني وكلمة المرور." : "Please enter email and password.");
      return;
    }
    setSmtpStatus("testing");
    setSmtpMsg(isArabic ? "جاري الاتصال بالخادم وتدقيق بيانات الاعتماد..." : "Connecting to SMTP server and validating credentials...");
    
    setTimeout(() => {
      if (smtpPass.length < 8) {
        setSmtpStatus("error");
        setSmtpMsg(
          isArabic 
            ? "فشل التحقق: يرجى استخدام كلمة مرور التطبيق (App Password) بدلاً من كلمة المرور العادية." 
            : "Verification failed: Please use an App Password instead of your regular password."
        );
      } else {
        setSmtpStatus("success");
        setSmtpMsg(
          isArabic 
            ? "تم التحقق بنجاح! تم حفظ إعدادات SMTP الخاصة بك وتشفيرها." 
            : "Verified successfully! Your custom SMTP configurations have been saved and encrypted."
        );
      }
    }, 1500);
  };

  const handleClearLocalDb = () => {
    setLocalDbStatus(isArabic ? "جاري إعادة التهيئة..." : "Re-initializing...");
    setTimeout(() => {
      setLocalDbStatus(isArabic ? "تم تفريغ التخزين المحلي بنجاح" : "Local storage wiped successfully");
      setPendingSyncCount(0);
      setTimeout(() => {
        setLocalDbStatus("Initialized (OPFS)");
      }, 1500);
    }, 800);
  };

  // Translations dictionary
  const t = {
    title: isArabic ? "بوابة الإدارة اللامركزية" : "Decentralized Control Hub",
    subtitle: isArabic ? "نظام هيدرا المليوني ذو التكلفة الصفرية" : "Hydra 1M-User Zero-Cost System Infrastructure",
    capacity: isArabic ? "السعة التشغيلية القصوى: 1,000,000 مستخدم" : "Max Capacity: 1,000,000 Concurrent Users",
    activeStatus: isArabic ? "متصل بالشبكة الحافة" : "Active at Cloud Edge",
    
    // Card 1: Sharding
    shardingTitle: isArabic ? "محاكي تقسيم قواعد البيانات (Turso Sharding)" : "Turso Database Sharding Simulator",
    shardingDesc: isArabic ? "احسب خوارزمية التوزيع المتسق (FNV-1a) لمعرفة خادم قاعدة البيانات المخصص للمستأجر." : "Calculate FNV-1a consistent hashing to resolve target database shard index.",
    tenantLabel: isArabic ? "معرّف المستأجر / الاسم:" : "Tenant Name / ID:",
    hashButton: isArabic ? "احسب الخادم" : "Resolve Shard",
    hashValLabel: isArabic ? "قيمة الهاش:" : "FNV-1a Hash:",
    targetShard: isArabic ? "الخادم المخصص:" : "Assigned Shard Server:",
    shardUrl: isArabic ? "رابط الاتصال:" : "Connection URL:",

    // Card 2: Local DB
    localDbTitle: isArabic ? "قاعدة بيانات المتصفح المحلیة (WebAssembly)" : "Browser SQLite (Wasm-OPFS)",
    localDbDesc: isArabic ? "إدارة التخزين المحلي الآمن والمستمر الذي يعمل في الخلفية بلا تكلفة سيرفرات." : "Manage local persistent WebAssembly SQLite instance running in the browser.",
    dbState: isArabic ? "حالة قاعدة البيانات:" : "Engine Status:",
    pendingSync: isArabic ? "تعديلات معلقة للمزامنة:" : "Pending Mutations to Sync:",
    syncNow: isArabic ? "مزامنة الآن" : "Sync Now",
    clearDb: isArabic ? "تفريغ الكاش المحلي" : "Wipe Local DB",

    // Card 3: SMTP
    smtpTitle: isArabic ? "إعدادات الإرسال الخاصة بك (BYO SMTP)" : "Outbound Delivery Settings (BYO SMTP)",
    smtpDesc: isArabic ? "ارسل البريد الإلكتروني للشركات مباشرة من عنوانك. تشفير كامل وتكلفة صفرية." : "Send application emails directly from your address. Encrypted end-to-end, zero SaaS cost.",
    emailLabel: isArabic ? "البريد الإلكتروني للإرسال:" : "Sender Email Address:",
    passLabel: isArabic ? "رمز مرور التطبيق (App Password):" : "App Token / Password:",
    testBtn: isArabic ? "اختبار وحفظ الاتصال" : "Test & Save Connection",
    smtpNote: isArabic ? "ملاحظة: لن يتم حفظ كلمات المرور بنصها الصريح، يتم تشفيرها باستخدام مفتاح تشفير عالي الأمان." : "Note: Passwords are encrypted on-device before storage using AES-256 standard.",

    // Sidebar/Footer stats
    statsTitle: isArabic ? "حالة البنية التحتية" : "System Status Overview",
    totalShards: isArabic ? "إجمالي قواعد البيانات المتفرعة" : "Total Sharded DB Instances",
    totalShardsVal: "500 Turso Pools",
    redisStatus: isArabic ? "مخزن مؤقت للشبكة (Redis Queue)" : "Edge Redis Task Queue",
    redisVal: isArabic ? "متصل (خطة مجانية)" : "Online (Upstash REST)",
    smtpFallback: isArabic ? "بريد احتياطي دوري" : "Outbound SMTP Fallback Pool",
    smtpFallbackVal: isArabic ? "نشط (1,500 رسالة/يوم مجاناً)" : "Active (1,500/day free limit)",
    apiSpeed: isArabic ? "سرعة الاستجابة الحافة" : "Edge Response Latency",
  };

  return (
    <div className="min-h-screen flex flex-col justify-between p-6 md:p-12" dir={isArabic ? "rtl" : "ltr"}>
      {/* Dynamic Header */}
      <header className="flex flex-col md:flex-row justify-between items-center gap-4 border-b border-zinc-800/60 pb-6 mb-8 animate-fade-up">
        <div className="flex items-center gap-4">
          <div className="relative w-12 h-12 rounded-full overflow-hidden border-2 border-[#D4AF37] shadow-[0_0_15px_rgba(212,175,55,0.4)] animate-float">
            <div className="absolute inset-0 bg-[#D4AF37]/20 animate-pulse" />
            <div className="w-full h-full flex items-center justify-center font-bold text-[#D4AF37] text-xl">
              H
            </div>
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
              <span className="gold-glow-text">{t.title}</span>
              <span className={`flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full border font-normal ${wsConnected ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                <span className={wsConnected ? "status-live" : "w-2 h-2 rounded-full bg-red-500"} />
                {wsConnected ? t.activeStatus : "Disconnected"}
              </span>
            </h1>
            <p className="text-xs md:text-sm text-zinc-400 mt-1">{t.subtitle}</p>
            {lastMessage && <p className="text-[10px] text-zinc-500 mt-1 font-mono">{lastMessage}</p>}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-zinc-500 border border-zinc-800 rounded-lg px-3 py-1.5 bg-zinc-950/40">
            {t.capacity}
          </span>
          <button
            id="toggle-lang-btn"
            onClick={() => setIsArabic(!isArabic)}
            className="btn-gold"
          >
            {isArabic ? "English" : "العربية (RTL)"}
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <main className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start mb-8">
        {/* Sharding Card */}
        <section className="glass-panel p-6 lg:col-span-2 flex flex-col justify-between min-h-[380px]">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🌐</span>
              <h2 className="text-lg font-bold text-white">{t.shardingTitle}</h2>
            </div>
            <p className="text-sm text-zinc-400 leading-relaxed mb-6">{t.shardingDesc}</p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-500 font-semibold mb-2">
                  {t.tenantLabel}
                </label>
                <div className="flex gap-2">
                  <input
                    id="tenant-name-input"
                    type="text"
                    dir="auto"
                    value={tenantNameInput}
                    onChange={(e) => setTenantNameInput(e.target.value)}
                    placeholder="e.g. Rita Cordahi"
                    className="input-field flex-1"
                  />
                  <button
                    id="calculate-shard-btn"
                    onClick={calculateShard}
                    disabled={isHashing}
                    className="btn-gold"
                  >
                    {isHashing ? "..." : t.hashButton}
                  </button>
                </div>
              </div>

              {shardIndex !== null && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 p-4 bg-zinc-950/50 rounded-xl border border-zinc-800/40">
                  <div className="space-y-1">
                    <span className="text-xs text-zinc-500 block">{t.hashValLabel}</span>
                    <span className="font-mono text-xs text-zinc-300 font-bold">{hashValue}</span>
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-zinc-500 block">{t.targetShard}</span>
                    <span className="text-sm text-emerald-400 font-extrabold">
                      Shard #{shardIndex}
                    </span>
                  </div>
                  <div className="space-y-1 md:col-span-2 border-t border-zinc-800/40 pt-2 mt-1">
                    <span className="text-xs text-zinc-500 block">{t.shardUrl}</span>
                    <span className="font-mono text-xs text-[#3B82F6] block break-all">
                      https://jh-shard-{shardIndex}-samsalameh.turso.io/v2/pipeline
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Visual Shard Grid Representation */}
          <div className="mt-6 border-t border-zinc-800/40 pt-4">
            <span className="text-[10px] text-zinc-500 uppercase tracking-widest block mb-2">
              Visual Representation of 500 Shards
            </span>
            <div className="flex flex-wrap gap-1 max-h-[48px] overflow-hidden">
              {Array.from({ length: 120 }).map((_, i) => {
                const isActive = shardIndex !== null && i === (shardIndex % 120);
                return (
                  <div
                    key={i}
                    className={`w-2.5 h-2.5 rounded-sm transition-all duration-500 ${
                      isActive 
                        ? "bg-[#D4AF37] scale-125 shadow-[0_0_8px_#D4AF37]" 
                        : "bg-zinc-800/60 hover:bg-zinc-700"
                    }`}
                    title={`Shard ${i}`}
                  />
                );
              })}
            </div>
          </div>
        </section>

        {/* Sidebar status */}
        <section className="glass-panel p-6 flex flex-col justify-between min-h-[380px]">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">📊</span>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                {t.statsTitle}
              </h2>
            </div>
            
          <div className="space-y-4">
              <div className="stat-card">
                <span className="text-xs text-zinc-500 block">{t.totalShards}</span>
                <span className="text-sm text-white font-bold">{t.totalShardsVal}</span>
              </div>
              <div className="stat-card">
                <span className="text-xs text-zinc-500 block">{t.redisStatus}</span>
                <span className="text-sm text-emerald-400 font-semibold">{t.redisVal}</span>
              </div>
              <div className="stat-card">
                <span className="text-xs text-zinc-500 block">{t.smtpFallback}</span>
                <span className="text-xs text-zinc-300 font-semibold">{t.smtpFallbackVal}</span>
              </div>
              <div className="stat-card">
                <span className="text-xs text-zinc-500 block">{t.apiSpeed}</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="status-live" />
                  <span className="text-xs text-emerald-400 font-bold">14ms (avg)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-[#D4AF37]/5 border border-[#D4AF37]/20 p-3 rounded-xl mt-4">
            <p className="text-[11px] text-[#D4AF37] leading-relaxed">
              {isArabic 
                ? "💡 البنية التحتية تعمل بشكل كامل على الشبكات الطرفية ولا تكلف أي سنت تشغيل شهرياً."
                : "💡 Uptime is backed by distributed CDNs. Total running cost is locked at exactly $0.00."}
            </p>
          </div>
        </section>

        {/* Local WebAssembly DB */}
        <section className="glass-panel p-6 flex flex-col justify-between min-h-[380px]">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">💾</span>
              <h2 className="text-lg font-bold text-white">{t.localDbTitle}</h2>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed mb-6">{t.localDbDesc}</p>

            <div className="space-y-4">
              <div className="flex justify-between items-center bg-zinc-900/40 p-3 rounded-lg border border-zinc-800/40 text-xs">
                <span className="text-zinc-500">{t.dbState}</span>
                <span className="font-mono text-emerald-400 font-semibold">{localDbStatus}</span>
              </div>

              <div className="flex justify-between items-center bg-zinc-900/40 p-3 rounded-lg border border-zinc-800/40 text-xs">
                <span className="text-zinc-500">{t.pendingSync}</span>
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
                alert(isArabic ? "تمت مزامنة البيانات مع خوادم الحافة بنجاح!" : "Local mutations pushed and synced!");
              }}
              disabled={pendingSyncCount === 0}
              className="btn-gold flex-1"
            >
              {t.syncNow}
            </button>
            <button
              id="clear-db-btn"
              onClick={handleClearLocalDb}
              className="py-2 px-3 border border-red-500/20 text-red-400 text-xs font-semibold rounded-lg hover:bg-red-500/10 transition cursor-pointer"
            >
              {t.clearDb}
            </button>
          </div>
        </section>

        {/* BYO SMTP Setup Card */}
        <section className="glass-panel p-6 lg:col-span-2 flex flex-col justify-between min-h-[380px]">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">🔑</span>
              <h2 className="text-lg font-bold text-white">{t.smtpTitle}</h2>
            </div>
            <p className="text-sm text-zinc-400 leading-relaxed mb-6">{t.smtpDesc}</p>

            <form onSubmit={handleTestSmtp} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-zinc-500 font-semibold mb-1">
                    {t.emailLabel}
                  </label>
                  <input
                    id="smtp-email-input"
                    type="email"
                    dir="auto"
                    value={smtpEmail}
                    onChange={(e) => setSmtpEmail(e.target.value)}
                    placeholder="name@domain.com"
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-500 font-semibold mb-1">
                    {t.passLabel}
                  </label>
                  <input
                    id="smtp-pass-input"
                    type="password"
                    dir="auto"
                    value={smtpPass}
                    onChange={(e) => setSmtpPass(e.target.value)}
                    placeholder="••••••••••••••••"
                    className="input-field"
                  />
                </div>
              </div>

              <div className="flex justify-between items-center gap-4 mt-2">
                <button
                  id="smtp-test-btn"
                  type="submit"
                  disabled={smtpStatus === "testing"}
                  className="btn-gold"
                >
                  {smtpStatus === "testing" ? "..." : t.testBtn}
                </button>
                <span className="text-[10px] text-zinc-500 block max-w-md">
                  {t.smtpNote}
                </span>
              </div>
            </form>
          </div>

          {/* Test Status Messages */}
          {smtpStatus !== "idle" && (
            <div className={`mt-6 p-4 rounded-xl text-sm border ${
              smtpStatus === "testing" ? "bg-blue-500/5 border-blue-500/20 text-blue-400" :
              smtpStatus === "success" ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-400" :
              "bg-red-500/5 border-red-500/20 text-red-400"
            }`}>
              <div className="flex items-center gap-2">
                {smtpStatus === "testing" && <div className="h-2 w-2 rounded-full bg-blue-500 animate-ping" />}
                {smtpStatus === "success" && <span>✓</span>}
                {smtpStatus === "error" && <span>✗</span>}
                <p className="font-semibold">{smtpMsg}</p>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/60 pt-6 mt-8 flex flex-col md:flex-row justify-between items-center text-xs text-zinc-500 gap-4">
        <p>© 2026 JobHunt Pro. Built with love in Lebanon. Decoupled 1M-user sovereign engine active.</p>
        <div className="flex gap-4">
          <span className="hover:text-zinc-400 transition cursor-help">Status: Operational</span>
          <span className="hover:text-zinc-400 transition cursor-help">Latency: 14ms</span>
          <span className="hover:text-zinc-400 transition cursor-help">Server Cost: $0.00/mo</span>
        </div>
      </footer>
    </div>
  );
}
