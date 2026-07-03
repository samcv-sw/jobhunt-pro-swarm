# 🚀 JobHunt Pro - The Ultimate System Blueprint

Ahlan dear! Hayda l blueprint l mfasal la kl chi b project "JobHunt Pro" taba3ak.
Fina n2assem l project la Front-end, Back-end, w kif byeshteghlo ma3 ba3d (Architecture & Workflow), w kl l details lli talabta.

## 🎨 1. Front-end (HTML, CSS, JavaScript & UI)
L wajeha l amemiye lli byotfa3al ma3a l user w btefroz l design.
- **HTML / Templates**: Kteer mn l pages maktoubin b HTML w mawsoulin b Python (Jinja2/Flask). 3endak `templates/` folder fiyo l pages mtl dashboard, login, register, w landing page. Haydol l pages dynamically byet3abbo data mn l server.
- **CSS**: Bted3am l styling, design, w animations ta te3te l user tajribe premium. Fiya support lal RTL (Right-to-Left) la ykoun l design mratab bl 3arabi w bya3mel auto-flip lal icons w layout (CSS Logical Properties).
- **JavaScript (Vanilla & Fetch API)**: Byet7akam bl dynamic actions (mtl submit forms, upload CV, micro-animations, w yjib data mn l backend bala ma y3mel refresh lal page).
- **Telegram Miniapp**: 3endak kaman frontend mkhassas lal Telegram `telegram_miniapp/` (HTML/JS/CSS) ta ykhalik tefta7 l dashboard ghuwa Telegram direct.
- **Chrome Extension**: Mawsoule b frontend sghir b `chrome_extension/` lte2dar ta3mel scrape w t3abe data mn l browser.

## ⚙️ 2. Back-end (Python, API, Web Server)
L mo7arek (Engine) lli byoshrf 3a kel l 3amaliyat.
- **app_v2.py (Main Server)**: Hayda l malaf l asasi. Fiyo l API routes, authentication, w routing lal web pages. (Bado refactoring ba3den la2anno kbeer).
- **Database (Neon PostgreSQL & SQLite)**: L data (users, jobs, wallets) bten7afaz 3a Neon PostgreSQL bl cloud, w fi `pg_sqlite_shim.py` btarjem commands SQLite la Postgres ta l code ykoun compatible everywhere bala errors.
- **Authentication & Security**: Byesta3mel Cookies mshafra bteb2a 30 yom la login/register system.
- **Aegis WAF & Panic Mode**: Bte7me l backend mn l SQL Injections w XSS attacks (`aegis_shield.py`). Kaman fi "Panic Mode" (`iron_cloak.py`) byekhfe l dashboard w byotla3 blog 3ade eza hada 3emil inspection aw audit.

## 🤖 3. AI & Scrapers (The Swarm Intelligence)
Hayda l system lli bta3mel l se7er kllo bl background:
- **Scraping Engine**: Scrapers (`multi_source_scraper.py`, `pa_job_scraper.py`) bteb7as b 7 masader (LinkedIn, Indeed, Glassdoor, etc.) b nafs l wa2t (Concurrent Threads).
- **Stealth Bots**: `stealth.py` byekhde3 l anti-bot systems w bya3mil fake hardware (mtl Apple M3 Max) w bya3tike IP Googlebot ta ma yontor block abadan.
- **AI ATS Matcher & Resume Tailoring**: `ats_matcher.py` w `ai_tailor.py` byekhdo l Job Description w l CV taba3 l user, w byesta3mlo AI (Groq/LLaMA 3) ta y3adlo l CV w ydeefo keywords la yonja7 bl ATS.
- **Email Rotator Engine**: 13 Gmail accounts bya3mlo rotation (`email_rotator_pool.py`) ta yeb3ato applications bala ma yn3amallon spam.

## 🔄 4. Kif byeshteghlo ma3 ba3d (The Workflow)
1. **Onboarding**: L user byfout 3al **Front-end** (landing page), bya3mel sign-up w bya3mel upload lal CV.
2. **Data Storage**: L data btenba3at lal **Back-end** (`app_v2.py`) w bten7afaz bl Neon Database.
3. **Trigger Scrapers**: L user byotlob ydawer 3a wazayef, l **Back-end** byo2mor l **Scrapers** yshaghlo l stealth mode w yjibo jobs mnasbi.
4. **AI Processing**: L **AI System** byo2ra l jobs, byzabet l CV, w byekteb Cover Letter mkhassase lal sharike.
5. **Execution**: L **Email Rotator** byeb3at l applications lal sherkat.
6. **Live Updates**: L **Front-end** byet7adas w byfarje l user l progress 3al Dashboard (kam wazife t2addam 3laya, l interviews, w statistics).

## ☁️ 5. Deployment & Cloud
- **PythonAnywhere**: L server l asasi lli 3le l website live. Fi script `pa_auto_renew.py` (via GitHub Actions) bya3mel login w byjaded l free plan kel shahren automatically, ya3ne byedall shaghal 24/7 forever (0$).
- **GitHub**: L source of truth taba3ak. Kl code modifications bten7at hon w bten3amal deploy.

---
Hayda howe l blueprint l kemil ya bro! Kl l a2sam (Front-end, Back-end, AI) mtartabin w byeshteghlo ka system wa7ad meshmet (God-Mode). Fik tsayvo 3endak w treja3lo ay wa2t! 🚀
