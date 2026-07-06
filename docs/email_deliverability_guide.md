# 📧 JobHunt Pro — Email Deliverability Guide
# دليل تحسين وصول الإيميلات (SPF / DKIM / DMARC)

> **الهدف:** ضمان وصول إيميلات JobHunt Pro إلى Inbox بدل Spam، وتجنب Ban من Gmail/Outlook/Hotmail
> **Why it matters:** Without proper DNS records, your emails go to spam. With 15+ SMTP accounts + 1000 Hotmail pool, you MUST set this up.

---

## 📋 Table of Contents
1. [Overview — How Email Deliverability Works](#1-overview)
2. [SMTP Accounts & Their Providers](#2-smtp-accounts)
3. [SPF Records Per Provider](#3-spf-records)
4. [DKIM Setup Per Provider](#4-dkim-setup)
5. [DMARC Policy Recommendation](#5-dmarc-policy)
6. [DNS Records — Step by Step](#6-dns-records)
7. [1000 Hotmail OAuth2 Pool](#7-hotmail-oauth2-pool)
8. [Testing & Monitoring](#8-testing)
9. [Troubleshooting Checklist](#9-troubleshooting)

---

## 1. Overview
<a id="1-overview"></a>

### The Email Authentication Trinity
| Record | What it does | Why it matters |
|--------|-------------|----------------|
| **SPF** | Lists which servers can send email for your domain | Prevents spoofing, reduces spam score |
| **DKIM** | Digital signature proving email wasn't tampered with | Builds sender reputation |
| **DMARC** | Tells receivers what to do if SPF/DKIM fail | Policy enforcement, visibility |

### How JobHunt Pro Sends Emails
- **15 Gmail/Outlook SMTP accounts** — each sends as their own email address
- **1000 Hotmail OAuth2 pool** — massive scale, auto-rotating
- **Brevo/Mailgun/SendGrid/Mailjet** — fallback providers
- **Target:** 2000+ emails/day with zero spam folder

> **Key Rule:** Each sender domain needs its own SPF record. If you're sending `samsalameh.cv@gmail.com`, Gmail handles SPF — but if you use a custom domain, YOU must set it up.

---

## 2. SMTP Accounts & Their Providers
<a id="2-smtp-accounts"></a>

### 🔴 الـ 15 حساب SMTP (شرح عربي-إنجليزي)

| # | Account Email | Provider | SMTP Server | Daily Cap | Set Up? |
|---|--------------|----------|-------------|-----------|---------|
| 1 | salamehnancy88@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 2 | demo_useruser2@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 3 | aurorafuture8@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 4 | luxurystoresvvip@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 5 | wyn27xauit@bbyuopsch.it.com | Disposable | smtp.gmail.com:587 | 100 | ⚠️ Custom domain → SPF needed |
| 6 | samsalameh.cv@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 7 | luxurystores888@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 8 | samsalameh.cv@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 9 | jrodriguez7476@live.hccc.edu | Outlook/EDU | smtp-mail.outlook.com:587 | 100 | ✅ Outlook auto-SPF |
| 10 | heribertstern968@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 11 | jaayivia275@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 12 | UgScheila@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 13 | demo_user.user01@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 14 | salamehsam33@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |
| 15 | paula.bassil.69@gmail.com | Gmail | smtp.gmail.com:587 | 100 | ✅ Gmail auto-SPF |

### Multi-Provider Free Tier Slots
| Name | Provider | SMTP Server | Config Var |
|------|----------|-------------|------------|
| sendgrid1 | SendGrid | smtp.sendgrid.net:587 | SENDGRID_KEY |
| mailjet1 | Mailjet | in-v3.mailjet.com:587 | MAILJET_KEY/MAILJET_SECRET |
| mailgun1 | Mailgun | smtp.mailgun.org:587 | MAILGUN_KEY |
| elastic1 | Elastic Email | smtp.elasticemail.com:2525 | ELASTIC_KEY |
| zoho1 | Zoho | smtp.zoho.com:587 | ZOHO_PASS |
| outlook2 | Outlook | smtp-mail.outlook.com:587 | OUTLOOK2_PASS |
| yahoo1 | Yahoo | smtp.mail.yahoo.com:587 | YAHOO_PASS |
| yandex1 | Yandex | smtp.yandex.com:587 | YANDEX_PASS |

### 🔥 1000 Hotmail OAuth2 Pool (v16.300+)
- **Type:** Auto-scaling OAuth2 pool via `data/hotmail_pool.json`
- **SMTP:** smtp-mail.outlook.com:587
- **Daily Cap:** 8000 emails (across all accounts)
- **Auth:** OAuth2 tokens (not passwords)
- **Config:** Add accounts to JSON file, system auto-loads them
- **No DNS changes needed** — Hotmail/Outlook handles SPF/DKIM automatically

---

## 3. SPF Records Per Provider
<a id="3-spf-records"></a>

### ما هو SPF؟
SPF (Sender Policy Framework) يحدد أي السيرفرات مسموح لها إرسال إيميلات بإسم الدومين الخاص بك.
بدون SPF، الإيميلات إما تروح Spam أو تُرفض.

### 🔵 Gmail (@gmail.com accounts)
**لا تحتاج أي إعدادات!** Google تدير SPF تلقائياً لجميع @gmail.com.
✅ `v=spf1 include:_spf.google.com ~all` (مضبوط تلقائياً)

### 🔵 Outlook/Hotmail (@outlook.com / @hotmail.com)
**لا تحتاج إعدادات.** Microsoft تدير SPF تلقائياً.
✅ `v=spf1 include:spf.protection.outlook.com ~all` (مضبوط تلقائياً)

### 🔵 Custom Domain (e.g., bbyuopsch.it.com)
إذا عندك حساب على دومين خاص (مثل account #5: wyn27xauit@bbyuopsch.it.com):

**DNS TXT Record:**
```
v=spf1 include:_spf.google.com include:spf.protection.outlook.com ~all
```

**Explanation:** This allows both Gmail and Outlook to send for this domain.

### 🔵 Brevo / SendGrid / Mailgun / Mailjet / Zoho
إذا تستخدم أي provider تاني:

| Provider | SPF include |
|----------|-------------|
| **SendGrid** | `include:sendgrid.net` |
| **Mailgun** | `include:mailgun.org` |
| **Mailjet** | `include:spf.mailjet.com` |
| **Brevo (Sendinblue)** | `include:_spf.brevo.com` |
| **Elastic Email** | `include:spf.elasticemail.com` |
| **Zoho** | `include:zoho.com` |
| **Yahoo** | `include:spf.mail.yahoo.com` |
| **Yandex** | `include:spf.yandex.com` |

### 🔵 Full SPF Record for Custom Domain (If you use multiple)
```
v=spf1 include:_spf.google.com include:spf.protection.outlook.com include:sendgrid.net include:mailgun.org include:spf.mailjet.com include:_spf.brevo.com include:spf.elasticemail.com include:zoho.com ~all
```

---

## 4. DKIM Setup Per Provider
<a id="4-dkim-setup"></a>

### ما هو DKIM؟
DKIM (DomainKeys Identified Mail) يضيف توقيع رقمي لكل إيميل. المستقبل يتأكد أن الإيميل حقيقي ولم يتم التلاعب به.
بدون DKIM: ⚠️ Spam score يرتفع، وقدامى Gmail يفضلون DKIM.

### 🔵 Gmail DKIM
Gmail accounts @gmail.com → **تلقائي بالكامل**، مش بحاجة أي شي.

لو عندك **Google Workspace (custom domain)**:
1. Open Google Admin Console → Apps → Gmail → Authenticate Email
2. Generate DKIM key
3. Add this **TXT record** to your DNS:

| Host | Type | Value |
|------|------|-------|
| `google._domainkey.yourdomain.com` | TXT | `v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb...` |

4. Click "Start Authentication" in Google Admin

### 🔵 Outlook/Hotmail DKIM
@outlook.com / @hotmail.com → **تلقائي**

### 🔵 SendGrid DKIM
1. Go to SendGrid Dashboard → Settings → Sender Authentication
2. Choose "Domain Authentication"
3. Add these DNS records:

| Host | Type | Value |
|------|------|-------|
| `s1._domainkey.yourdomain.com` | CNAME | `s1.domainkey.u123.wl.sendgrid.net` |
| `s2._domainkey.yourdomain.com` | CNAME | `s2.domainkey.u123.wl.sendgrid.net` |
| `em123.yourdomain.com` | CNAME | `u123.wl.sendgrid.net` |

### 🔵 Mailgun DKIM
1. Mailgun Dashboard → Domains → Your Domain → DNS Records
2. Add these:

| Host | Type | Value |
|------|------|-------|
| `krs._domainkey.yourdomain.com` | TXT | `k=rsa; p=MIGfMA0GCSqGSIb3...` |
| `email.yourdomain.com` | CNAME | `mailgun.org` |
| `*.email.yourdomain.com` | CNAME | `mailgun.org` |

### 🔵 Mailjet DKIM
1. Mailjet → Account Settings → Sender Domains → Add Domain
2. Verify by adding TXT record: `"mj-domainkey=your-domain-id"`
3. Add DKIM: Copy the `DKIM TXT` record from Mailjet dashboard

### 🔵 Zoho DKIM
1. Zoho Mail → Control Panel → DKIM → Add
2. Selector: `zoho` (default)
3. Add TXT record: `zoho._domainkey.yourdomain.com`

---

## 5. DMARC Policy Recommendation
<a id="5-dmarc-policy"></a>

### ما هو DMARC؟
DMARC يخبر Gmail/Outlook/Yahoo ماذا يفعلون إذا فشل SPF و DKIM معاً.
مثلاً: يرفض الإيميل (p=reject) أو يحطه في Spam (p=quarantine).

### 🟢 Recommended DMARC for JobHunt Pro

**DNS Record Name:** `_dmarc.yourdomain.com`
**Type:** TXT
**Value:**
```
v=DMARC1; p=quarantine; sp=quarantine; rua=mailto:dmarc-reports@yourdomain.com; ruf=mailto:dmarc-forensics@yourdomain.com; pct=100; fo=1
```

### Explanation of Fields
| Field | Value | Meaning |
|-------|-------|---------|
| `v` | DMARC1 | Version (always) |
| `p` | quarantine | Put failing emails in spam (not reject yet) |
| `sp` | quarantine | Same policy for subdomains |
| `rua` | email address | Where to send aggregate reports (XML weekly) |
| `ruf` | email address | Where to send forensic reports (per-failure) |
| `pct` | 100 | Apply to 100% of email |
| `fo` | 1 | Generate forensic report if SPF OR DKIM fails |

### DMARC Policy Progression
```
p=none → p=quarantine → p=reject
```
1. **Start with `p=none`** → Monitor reports for 2 weeks
2. **Move to `p=quarantine`** → After confirming no false positives
3. **Upgrade to `p=reject`** → Only when you're confident everything works

### DMARC Reports (rua)
بترسل تقارير XML أسبوعياً. تقدر تحللها باستخدام:
- https://dmarcian.com (free)
- https://mxtoolbox.com/Dmarc.aspx (free)
- https://www.dmarcanalyzer.com (limited free)

---

## 6. DNS Records — Step by Step
<a id="6-dns-records"></a>

### خطوات إضافة DNS Records (عام)

#### If using Cloudflare (recommended):
1. Login to Cloudflare → Select domain
2. Go to DNS → Records → Add Record
3. Choose type (TXT/CNAME)
4. Fill in Name & Value from the tables above
5. Save → Wait 5-30 min for propagation

#### If using your domain registrar:
1. Go to Domain Management → DNS / Zone Editor
2. Add the TXT/CNAME records
3. Important: Some registrars prepend domain name automatically
   - If hostname is `google._domainkey` and your domain is `example.com`
   - Some want just `google._domainkey`, others want `google._domainkey.example.com`
   - Check their format guide

### Quick Reference — DNS Records Checklist

| Priority | Record | Where | Purpose |
|----------|--------|-------|---------|
| 🔴 **MUST** | SPF TXT | Your DNS | Prevent spoofing, pass Gmail check |
| 🟡 **SHOULD** | DKIM TXT | Your DNS | Digital signature, build reputation |
| 🟢 **GOOD** | DMARC TXT | Your DNS | Policy + reports |
| ⚪ OPTIONAL | MX Record | Your DNS | If receiving email on this domain |
| ⚪ OPTIONAL | BIMI TXT | Your DNS | Logo in Gmail inbox |

---

## 7. Hotmail OAuth2 Pool (1000 Accounts)
<a id="7-hotmail-oauth2-pool"></a>

### What It Is
- **1000 Hotmail/Outlook accounts** created via automation
- **OAuth2 authentication** (not password-based) — Microsoft-approved flow
- **Auto-rotation:** system picks unused accounts and rotates daily
- **Rate limiting:** 8 emails/account/day max → 8000 emails/day total

### Setup
1. Run the Hotmail pool generator: `python3 scripts/hotmail_pool_generator.py`
2. Accounts saved to `data/hotmail_pool.json`
3. Each account gets OAuth2 tokens stored in `data/hotmail_oauth_cache.json`
4. System auto-loads and rotates

### DNS Note
Since all accounts are @hotmail.com / @outlook.com, **no custom DNS records needed**.
Microsoft's SPF/DKIM/DMARC apply automatically.

---

## 8. Testing & Monitoring
<a id="8-testing"></a>

### 🛠️ Test Your Setup

**1. SPF Check:**
```
nslookup -type=TXT yourdomain.com
```
Or: https://mxtoolbox.com/spf.aspx

**2. DKIM Check:**
```
nslookup -type=TXT google._domainkey.yourdomain.com
```
Or: https://www.dmarcanalyzer.com/dkim/dkim-check/

**3. DMARC Check:**
```
nslookup -type=TXT _dmarc.yourdomain.com
```
Or: https://mxtoolbox.com/Dmarc.aspx

**4. Send Test Email:**
- Send to: `check-auth@verifier.port25.com`
- You'll get an auto-response with full SPF/DKIM/DMARC analysis
- Or use: https://www.mail-tester.com (free)

### 📊 Monitoring Dashboard
Once DMARC is set up, you'll receive XML reports at the `rua` email address.
Parse them with: https://dmarcian.com/dmarc-report-parser/

---

## 9. Troubleshooting Checklist
<a id="9-troubleshooting"></a>

### مشكلة: الإيميلات بروح Spam | Why Emails Go to Spam

| ✅ Check | Fix |
|----------|-----|
| SPF record exists? | Add TXT record → see Section 3 |
| DKIM signature? | Setup DKIM → see Section 4 |
| DMARC policy? | Add _dmarc TXT → see Section 5 |
| Sending too fast? | Capped at 100/account/day (BanShield does this) |
| Content triggering spam? | Avoid: ALL CAPS, too many links, "free money" phrases |
| IP reputation? | Warm up new accounts: start 10/day, increase slowly |
| List hygiene? | Remove hard bounces immediately (system does this) |
| Unsubscribe link? | Every email has one (system adds automatically) |

### Quick Arabic Checklist
```
□ مضبوط SPF? → TXT record في DNS
□ مضبوط DKIM? → توقيع رقمي  
□ مضبوط DMARC? → p=quarantine على الأقل
□ Speed capping? → 100/account/day
□ Warm-up? → كل حساب جديد ابدأ ب 10-20/day
```

### Best Practices
1. **USE SUBDOMAINS** — Instead of `yourdomain.com`, use `mail.yourdomain.com`
   - Easier to manage SPF
   - If blacklisted, main domain stays clean
2. **WARM UP ACCOUNTS** — New accounts send 10/day → 30 → 50 → 100 over 2 weeks
3. **MONITOR BOUNCE RATES** — Under 3% is healthy. Over 5% → investigate
4. **ROTATE SENDING ADDRESSES** — System does this automatically (BanShield)
5. **KEEP SPF UNDER 10 LOOKUPS** — DNS query limit. JobHunt Pro config may exceed this for custom domains → consider subdomain

---

> 💡 **Pro Tip:** Running on PythonAnywhere? You can't add DNS records there. SPF/DKIM/DMARC are set at your **domain registrar** (Cloudflare / Namecheap / GoDaddy) not on the hosting platform.

> 🎯 **Final Note for Sam:** All @gmail.com and @outlook.com accounts are auto-secured. The ONLY time you need DNS changes is if you use a **custom domain** like `bbyuopsch.it.com`. For your 1000 Hotmail pool → zero DNS work needed.

