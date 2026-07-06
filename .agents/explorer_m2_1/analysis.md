# Arabic HTML Templates Deep Content & Visual Audit Report

**Audit Date**: 2026-07-06

## Executive Summary

This audit performs a deep analysis of 14 key Arabic HTML templates in the `web/templates/` folder against the global system rules and user specifications. The parameters evaluated include:
1. **Placeholder text detection** (e.g., TODO, Lorem Ipsum, Coming soon, محتوى قريباً).
2. **Visual theme alignment** (Dark gradient backgrounds, premium glassmorphism card styles).
3. **Interactions** (Presence of hover:transform and hover:box-shadow on buttons/links).
4. **Arabic Typography rules** (Use of Cairo/Tajawal, min 16px font-size, line-height 1.6-2.0, absolute absence of letter-spacing).
5. **Form field internationalization** (Presence of `dir="auto"` on all inputs, select, and textarea elements).
6. **RTL layout compatibility** (Use of CSS Logical Properties instead of physical properties like margin-left/padding-right).

---

## High-Level Matrix

| Template File | Dark Gradient BG | Glassmorphism | Buttons Hover | Typo Style (Min 16px) | Typo (No Letter-Spacing) | Form Input `dir="auto"` | Logical CSS | Placeholders |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `index_v3.html` | ✅ Yes | ✅ Yes | ❌ 15 missing | ❌ 4 under 16px | ✅ OK | ✅ All OK | ✅ Logical | ✅ None |
| `pricing_v3.html` | ❌ No | ✅ Yes | ❌ 2 missing | ❌ 1 under 16px | ✅ OK | ✅ All OK | ❌ 1 physical | ✅ None |
| `for_employers.html` | ❌ No | ❌ No | ❌ 10 missing | ✅ All >=16px | ✅ OK | ❌ 1 missing | ❌ 1 physical | ⚠️ 8 found |
| `trust.html` | ✅ Yes | ✅ Yes | ❌ 1 missing | ✅ All >=16px | ✅ OK | ✅ All OK | ❌ 1 physical | ✅ None |
| `services_v2.html` | ✅ Yes | ❌ No | ❌ 12 missing | ❌ 3 under 16px | ✅ OK | ✅ All OK | ✅ Logical | ⚠️ 2 found |
| `faq.html` | ❌ No | ❌ No | ✅ All OK | ✅ All >=16px | ✅ OK | ✅ All OK | ✅ Logical | ✅ None |
| `contact.html` | ❌ No | ✅ Yes | ❌ 1 missing | ✅ All >=16px | ✅ OK | ❌ 1 missing | ✅ Logical | ⚠️ 3 found |
| `dashboard_v3.html` | ✅ Yes | ✅ Yes | ❌ 7 missing | ❌ 27 under 16px | ❌ 2 violations | ❌ 1 missing | ✅ Logical | ⚠️ 2 found |
| `upload_cv_v2.html` | ❌ No | ❌ No | ❌ 12 missing | ✅ All >=16px | ✅ OK | ✅ All OK | ✅ Logical | ⚠️ 17 found |
| `ats_scorer.html` | ✅ Yes | ✅ Yes | ❌ 6 missing | ✅ All >=16px | ✅ OK | ✅ All OK | ✅ Logical | ⚠️ 6 found |
| `resume_tailor.html` | ❌ No | ❌ No | ❌ 5 missing | ❌ 3 under 16px | ✅ OK | ✅ All OK | ✅ Logical | ⚠️ 4 found |
| `wallet.html` | ❌ No | ❌ No | ❌ 20 missing | ❌ 5 under 16px | ✅ OK | ✅ All OK | ✅ Logical | ⚠️ 4 found |
| `war_room.html` | ✅ Yes | ✅ Yes | ❌ 4 missing | ❌ 10 under 16px | ❌ 12 violations | ✅ All OK | ✅ Logical | ✅ None |
| `battle_station.html` | ❌ No | ❌ No | ❌ 9 missing | ❌ 2 under 16px | ✅ OK | ✅ All OK | ✅ Logical | ✅ None |

---

## Detailed Template Audits

### `index_v3.html`

#### 1. Placeholder Text
- ✅ No placeholder texts or standard 'TODO'/'Lorem Ipsum' markers were found.

#### 2. Visual Theme & Style
- **Dark Gradient Background**: Detected. 
  - Classes: `['class="bg-layer bg-gradient"']`
  - Styles: `['background:var(--bg)', 'background:var(--bg)']`
- **Glassmorphism Card Style**: Detected. 
  - Verified selectors/classes on lines: 111, 2187, 2217

#### 3. Button/Link Hover Interactions
- ❌ 15 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 2307**: `<button class="btn" onclick="acceptCookies()">` (missing transform, missing shadow)
  - **Line 2439**: `<a class="fj-apply-btn" href="{{ job.url }}">` (missing transform, missing shadow)
  - **Line 2539**: `<a class="ats-scan-btn" href="/register">` (missing transform, missing shadow)
  - **Line 2562**: `<a class="ats-scan-btn" href="/register">` (missing transform, missing shadow)
  - **Line 2757**: `<button class="calc-tab active" onclick="showCalc('local')">` (missing transform, missing shadow)
  - **Line 2758**: `<button class="calc-tab" onclick="showCalc('worldwide')">` (missing transform, missing shadow)
  - **Line 2759**: `<button class="calc-tab" onclick="showCalc('remote')">` (missing transform, missing shadow)
  - **Line 2852**: `<a class="btn btn-cyan" href="/register?plan=starter">` (missing transform, missing shadow)
  - **Line 2871**: `<a class="btn btn-magenta" href="/register?plan=basic">` (missing transform, missing shadow)
  - **Line 2893**: `<a class="btn btn-cyan" href="/register?plan=pro">` (missing transform, missing shadow)
  - ... and 5 more buttons.

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', monospace, 'Cairo', 'JetBrains Mono',monospace, 'Cairo', 'Inter',-apple-system,BlinkMacSystemFont,sans-serif, 'Cairo', 'Inter',sans-serif, 'Cairo', 'Space Grotesk',sans-serif` | Classes: `None (inherits)`
- ❌ **Font-Size Violations** (4 instances where font size < 16px on Arabic content):
  - **Line 2666**: `<td class="highlight" style="color:var(--cyan);font-weight:800;font-size:14px">2$ مرة واحدة</td>`
  - **Line 3096**: `<div style="text-align:center"><div id="roiCost" style="font-family:'Cairo', 'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:var(--cyan)">$5</div><div style="font-size:10px;color:var(--muted)">تكلفة لمرة واحدة</div></div>`
  - **Line 3097**: `<div style="text-align:center"><div id="roiReturn" style="font-family:'Cairo', 'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:var(--green)">$50,000</div><div style="font-size:10px;color:var(--muted)">العائد السنوي</div></div>`
  - **Line 3098**: `<div style="text-align:center"><div id="roiMultiplier" style="font-family:'Cairo', 'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:var(--magenta)">{{ _('10,000x') }}</div><div style="font-size:10px;color:var(--muted)">مضاعف العائد</div></div>`
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `pricing_v3.html`

#### 1. Placeholder Text
- ✅ No placeholder texts or standard 'TODO'/'Lorem Ipsum' markers were found.

#### 2. Visual Theme & Style
- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.
- **Glassmorphism Card Style**: Detected. 
  - Verified selectors/classes on lines: 30, 31, 235, 295, 349...

#### 3. Button/Link Hover Interactions
- ❌ 2 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 523**: `<a class="btn {{ tier.button_class }}" href="{{ '/new-campaign' if is_logged_in else '/register' }}">` (missing transform, missing shadow)
  - **Line 654**: `<button class="toast-close-v3" onclick="document.getElementById('socialToastV3').classList.remove('show')">` (missing transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `var(--font-mono)` | Classes: `None (inherits)`
- ❌ **Font-Size Violations** (1 instances where font size < 16px on Arabic content):
  - **Line 541**: `<div style="color:var(--text-muted);font-size:12px;text-transform:uppercase;margin-bottom:16px;">حملات</div>`
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ❌ **Physical CSS Properties** detected (1 instances):
  - **Line 190**: `position: absolute; top: -14px; left: 50%; transform: translateX(calc(-50% * var(--text-x-direction, 1)));` (Matched: `['left: 50%']`)

---

### `for_employers.html`

#### 1. Placeholder Text
The following placeholder texts/attributes were detected:
- **Line 348**: `<input dir="auto" id="company_name" placeholder="مثال: Murex, Bank Audi..." required="" type="text"/>`
- **Line 352**: `<input dir="auto" id="job_title" placeholder="مثال: مهندس شبكات أول" required="" type="text"/>`
- **Line 356**: `<input dir="auto" id="location" placeholder="مثال: بيروت، لبنان" required="" type="text"/>`
- **Line 374**: `<input dir="auto" id="salary" placeholder="مثال: 2,500$ - 3,500$/شهر" type="text"/>`
- **Line 378**: `<input dir="auto" id="contact_email" placeholder="hr@yourcompany.com" required="" type="email"/>`
- **Line 383**: `<textarea dir="auto" id="description" placeholder="اشرح الدور، المسؤوليات، المتطلبات، وليش شركتك مكان رائع للعمل...`
- **Line 389**: `<input dir="auto" id="apply_url" placeholder="https://yourcompany.com/careers/..." type="url"/>`
- **Line 393**: `<input dir="auto" id="logo_url" placeholder="https://yourcompany.com/logo.png" type="url"/>`

#### 2. Visual Theme & Style
- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.
- ❌ **Glassmorphism Card Style**: Not explicitly detected via classes (`backdrop-blur`, `bg-white/`, `glass`).

#### 3. Button/Link Hover Interactions
- ❌ 10 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 202**: `<button class="btn" style="background:linear-gradient(135deg,#64748b,#475569);">` (missing transform, missing shadow)
  - **Line 217**: `<button class="btn" style="background:linear-gradient(135deg,var(--purple),#7c3aed);">` (missing transform, missing shadow)
  - **Line 232**: `<button class="btn" style="background:linear-gradient(135deg,var(--gold),#d97706);">` (missing transform, missing shadow)
  - **Line 248**: `<button class="btn" style="background:linear-gradient(135deg,#ec4899,#8b5cf6);">` (missing transform, missing shadow)
  - **Line 255**: `<button class="duration-btn selected" data-days="30" data-discount="0" onclick="selectDuration(30, 0, this)">` (has transform, missing shadow)
  - **Line 258**: `<button class="duration-btn" data-days="60" data-discount="10" onclick="selectDuration(60, 10, this)">` (has transform, missing shadow)
  - **Line 261**: `<button class="duration-btn" data-days="90" data-discount="17" onclick="selectDuration(90, 17, this)">` (has transform, missing shadow)
  - **Line 264**: `<button class="duration-btn" data-days="180" data-discount="25" onclick="selectDuration(180, 25, this)">` (has transform, missing shadow)
  - **Line 267**: `<button class="duration-btn" data-days="365" data-discount="42" onclick="selectDuration(365, 42, this)">` (has transform, missing shadow)
  - **Line 417**: `<button class="submit-btn" disabled="" id="submitBtn" type="submit">` (missing transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', inherit` | Classes: `None (inherits)`
- ✅ No font-size violations found (all Arabic content is >= 16px).
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ❌ **Missing `dir="auto"`** on 1 input/select/textarea elements:
  - **Line 360**: `<select id="category">`

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ❌ **Physical CSS Properties** detected (1 instances):
  - **Line 47**: `.price-card.popular::before { content:'🔥 الأكثر طلباً'; position:absolute; top:-12px; left: 50%; transform:translateX(-50%); background:linear-gradient(135deg,var(--purple),var(--pink)); color:#fff; font-size:.65em; font-weight:700; padding:4px 14px; border-radius:20px; white-space:nowrap; }` (Matched: `['left: 50%']`)

---

### `trust.html`

#### 1. Placeholder Text
- ✅ No placeholder texts or standard 'TODO'/'Lorem Ipsum' markers were found.

#### 2. Visual Theme & Style
- **Dark Gradient Background**: Detected. 
  - Classes: `['class="bg-layer bg-gradient"']`
  - Styles: `['background:var(--bg)', 'background:var(--bg)']`
- **Glassmorphism Card Style**: Detected. 
  - Verified selectors/classes on lines: 23

#### 3. Button/Link Hover Interactions
- ❌ 1 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 448**: `<a class="btn-cyan" href="/register">` (missing transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', sans-serif, 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif` | Classes: `None (inherits)`
- ✅ No font-size violations found (all Arabic content is >= 16px).
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ❌ **Physical CSS Properties** detected (1 instances):
  - **Line 62**: `position:fixed;top:12px;left: 50%;transform:translateX(50%);z-index:1000;` (Matched: `['left: 50%']`)

---

### `services_v2.html`

#### 1. Placeholder Text
The following placeholder texts/attributes were detected:
- **Line 978**: `<input dir="auto" id="customerName" placeholder="مثال: فلان الفلاني" required="" type="text"/>`
- **Line 980**: `<input dir="auto" id="customerEmail" placeholder="مثال: flan@example.com" required="" type="email"/>`

#### 2. Visual Theme & Style
- **Dark Gradient Background**: Detected. 
  - Styles: `['background: var(--bg)']`
- ❌ **Glassmorphism Card Style**: Not explicitly detected via classes (`backdrop-blur`, `bg-white/`, `glass`).

#### 3. Button/Link Hover Interactions
- ❌ 12 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 756**: `<a class="btn-nav" href="/register">` (missing transform, missing shadow)
  - **Line 806**: `<button class="btn-buy btn-buy-micro" onclick="addToCart('{{ s.id }}', '{{ s.name }}', {{ s.price }})">` (missing transform, missing shadow)
  - **Line 835**: `<button class="btn-buy btn-buy-standard" onclick="addToCart('{{ s.id }}', '{{ s.name }}', {{ s.price }})">` (missing transform, missing shadow)
  - **Line 864**: `<button class="btn-buy btn-buy-premium" onclick="addToCart('{{ s.id }}', '{{ s.name }}', {{ s.price }})">` (missing transform, missing shadow)
  - **Line 894**: `<button class="btn-bouquet" onclick="addToCart('{{ b.id }}', '{{ b.name }}', {{ b.price }}, true)">` (missing transform, missing shadow)
  - **Line 937**: `<a class="btn-buy btn-buy-premium" href="/register" style="padding: 14px 40px; font-size: 14px;">` (missing transform, missing shadow)
  - **Line 944**: `<button class="cart-toggle" id="cartToggle" onclick="toggleCart()">` (missing transform, missing shadow)
  - **Line 954**: `<button class="cart-close" onclick="toggleCart()">` (missing transform, missing shadow)
  - **Line 964**: `<button class="cart-checkout" onclick="openCheckoutModal()">` (missing transform, missing shadow)
  - **Line 970**: `<button class="modal-close" onclick="closeModal()">` (missing transform, missing shadow)
  - ... and 2 more buttons.

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', var(--mono), 'Cairo', var(--font)` | Classes: `None (inherits)`
- ❌ **Font-Size Violations** (3 instances where font size < 16px on Arabic content):
  - **Line 924**: `<div style="color:var(--muted); font-size:15px; margin-bottom: 12px;">العملات الرقمية المقبولة</div>`
  - **Line 937**: `<a class="btn-buy btn-buy-premium" href="/register" style="padding: 14px 40px; font-size: 14px;">أنشئ حساب مجاني</a>`
  - **Line 973**: `<p style="color:var(--muted); font-size:15px; margin-bottom:8px;">أدخل بياناتك لتستلم طلبك عبر الإيميل.</p>`
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `faq.html`

#### 1. Placeholder Text
- ✅ No placeholder texts or standard 'TODO'/'Lorem Ipsum' markers were found.

#### 2. Visual Theme & Style
- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.
- ❌ **Glassmorphism Card Style**: Not explicitly detected via classes (`backdrop-blur`, `bg-white/`, `glass`).

#### 3. Button/Link Hover Interactions
- ✅ All detected button/link elements properly declare hover transform and shadow classes.

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', 'Inter', -apple-system, sans-serif` | Classes: `None (inherits)`
- ✅ No font-size violations found (all Arabic content is >= 16px).
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `contact.html`

#### 1. Placeholder Text
The following placeholder texts/attributes were detected:
- **Line 95**: `<input autocomplete="name" class="glass-input" dir="auto" id="name" name="name" placeholder="اسمك الكريم" required="" type="text" value="{{ user_name or '' }}"/>`
- **Line 99**: `<input autocomplete="email" class="glass-input" dir="auto" id="email" name="email" placeholder="you@example.com" required="" type="email" value="{{ user_email or '' }}"/>`
- **Line 117**: `<textarea class="glass-input" dir="auto" id="message" name="message" placeholder="خبرنا شو ببالك... فيك تحط تفاصيل قد ما بدك — منقرا كل كلمة." required=""></textarea>`

#### 2. Visual Theme & Style
- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.
- **Glassmorphism Card Style**: Detected. 
  - Verified selectors/classes on lines: 31, 32, 33, 34, 95...

#### 3. Button/Link Hover Interactions
- ❌ 1 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 119**: `<button class="btn-submit" type="submit">` (missing transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', 'Inter', sans-serif` | Classes: `None (inherits)`
- ✅ No font-size violations found (all Arabic content is >= 16px).
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ❌ **Missing `dir="auto"`** on 1 input/select/textarea elements:
  - **Line 104**: `<select class="glass-input" id="subject" name="subject" required="">`

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `dashboard_v3.html`

#### 1. Placeholder Text
The following placeholder texts/attributes were detected:
- **Line 484**: `<input class="w-full rounded-lg border border-white/10 bg-slate-800 p-2.5 text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" id="smtpEmail" placeholder="you@domain.com" type="email" dir="auto"/>`
- **Line 488**: `<input class="w-full rounded-lg border border-white/10 bg-slate-800 p-2.5 text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" id="smtpPass" placeholder="16-digit App Password" type="password" dir="auto"/>`

#### 2. Visual Theme & Style
- **Dark Gradient Background**: Detected. 
  - Classes: `['class="flex items-center gap-2 rounded-full border border-blue-500/40 bg-gradient-to-r from-indigo-500/20 to-blue-500/20 px-4 py-2 text-sm font-semibold text-blue-300 shadow-[0_0_15px_rgba(59,130,246,0.3)] animate-pulse-slow"', 'class="flex items-center gap-2 rounded-full border border-emerald-500/40 bg-gradient-to-r from-indigo-500/20 to-emerald-500/20 px-4 py-2 text-sm font-semibold text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)] animate-pulse-slow"', 'class="flex items-center gap-2 rounded-full border border-pink-500/40 bg-gradient-to-r from-indigo-500/20 to-pink-500/20 px-4 py-2 text-sm font-semibold text-pink-300 shadow-[0_0_15px_rgba(236,72,153,0.3)] animate-pulse-slow"', 'class="rounded-xl border border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 to-slate-900/80 p-6 backdrop-blur-md reveal"']`
  - Styles: `['background-image:linear-gradient']`
- **Glassmorphism Card Style**: Detected. 
  - Verified selectors/classes on lines: 6, 14, 51, 77, 85...

#### 3. Button/Link Hover Interactions
- ❌ 7 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 77**: `<button class="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 transition-colors hover:bg-white/10 hover:text-white" onclick="document.getElementById('shortcutModal').showModal()" title="اختصارات لوحة المفاتيح">` (has transform, missing shadow)
  - **Line 160**: `<button class="rounded-md px-3 py-1.5 text-xs font-medium transition-colors bg-indigo-500/20 text-indigo-300" onclick="switchChart('bar',this)">` (has transform, missing shadow)
  - **Line 161**: `<button class="rounded-md px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:text-white" onclick="switchChart('line',this)">` (has transform, missing shadow)
  - **Line 162**: `<button class="rounded-md px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:text-white" onclick="switchChart('doughnut',this)">` (has transform, missing shadow)
  - **Line 287**: `<button class="rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white">` (missing transform, missing shadow)
  - **Line 471**: `<button class="text-slate-400 hover:text-white" onclick="document.getElementById('smtpModal').close()">` (missing transform, missing shadow)
  - **Line 491**: `<button class="w-full rounded-lg bg-indigo-600 py-3 font-bold text-white transition-all hover:bg-indigo-500 mt-4 flex justify-center items-center gap-2" id="smtpConnectBtn" onclick="connectSmtp()">` (has transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `None (inherits)` | Classes: `None (inherits)`
- ❌ **Font-Size Violations** (27 instances where font size < 16px on Arabic content):
  - **Line 88**: `<p class="text-sm text-emerald-100/70">{{ _('اربط حساب بريدك الإلكتروني المهني. سيقوم الذكاء الاصطناعي لدينا تلقائياً بتحسين أنماط الإرسال الخاصة بك واستخدام توجيه IP المخصص لضمان أعلى معدلات الاستجابة من أصحاب العمل.') }}</p>`
  - **Line 111**: `<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:600;">الطلبات النشطة</div>`
  - **Line 112**: `<div style="font-size:10px;color:#4b5563;margin-block-start:4px;">تم الإرسال عبر المنصات</div>`
  - **Line 119**: `<span style="font-size:10px;font-weight:700;color:#4ade80;background:rgba(74,222,128,0.1);padding:3px 8px;border-radius:20px;">عالي</span>`
  - **Line 122**: `<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:600;">معدل التوافق</div>`
  - ... and 22 more size violations.
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ❌ **Letter-Spacing Violations** (2 instances where letter-spacing/tracking classes are used on Arabic text):
  - **Line 173**: `<h3 class="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">إجراءات سريعة</h3>`
  - **Line 195**: `<h3 class="mb-4 text-xs font-semibold uppercase tracking-wider text-indigo-300">الترسانة النشطة</h3>`

#### 5. Form Inputs `dir="auto"` Alignment
- ❌ **Missing `dir="auto"`** on 1 input/select/textarea elements:
  - **Line 477**: `<select class="w-full rounded-lg border border-white/10 bg-slate-800 p-2.5 text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" id="smtpProvider">`

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `upload_cv_v2.html`

#### 1. Placeholder Text
The following placeholder texts/attributes were detected:
- **Line 546**: `<textarea class="large" dir="auto" id="cvText" placeholder="Paste your entire CV / resume text here...`
- **Line 569**: `<div class="form-group"><label for="fullName">{{ _('Full Name') }} <span style="color:#f87171;">*</span></label><input dir="auto" id="fullName" placeholder="e.g. Sam Salameh" type="text"/></div>`
- **Line 570**: `<div class="form-group"><label for="email">{{ _('Email') }}</label><input dir="auto" id="email" placeholder="your@email.com" type="email"/></div>`
- **Line 573**: `<div class="form-group"><label for="phone">الهاتف</label><input dir="auto" id="phone" placeholder="+961 3 123 456" type="text"/></div>`
- **Line 574**: `<div class="form-group"><label for="location">الموقع</label><input dir="auto" id="location" placeholder="بيروت، لبنان" type="text"/></div>`
- **Line 577**: `<div class="form-group"><label for="currentTitle">المسمى الوظيفي الحالي</label><input dir="auto" id="currentTitle" placeholder="مهندس شبكات أول" type="text"/></div>`
- **Line 581**: `<div class="form-group"><label for="education">التعليم</label><input dir="auto" id="education" placeholder="بكالوريوس هندسة" type="text"/></div>`
- **Line 582**: `<div class="form-group"><label for="linkedin">لينكد إن</label><input dir="auto" id="linkedin" placeholder="https://linkedin.com/in/..." type="url"/></div>`
- **Line 584**: `<div class="form-group"><label for="skillsInput">المهارات (مفصولة بفاصلة)</label><input dir="auto" id="skillsInput" placeholder="Cisco, Python, Linux, AWS, MikroTik, Fortinet..." type="text"/><div class="tag-list" id="skillsTags"></div></div>`
- **Line 585**: `<div class="form-group"><label for="certsInput">الشهادات</label><input dir="auto" id="certsInput" placeholder="CCNA, NSE, MTCNA..." type="text"/><div class="tag-list" id="certsTags"></div></div>`
- **Line 586**: `<div class="form-group"><label for="langsInput">اللغات</label><input dir="auto" id="langsInput" placeholder="English, Arabic, French..." type="text"/><div class="tag-list" id="langsTags"></div></div>`
- **Line 587**: `<div class="form-group"><label for="experienceInput">الخبرات (مفصولة بفاصلة)</label><input dir="auto" id="experienceInput" placeholder="Ogero (2020-2023), Touch (2018-2020)..." type="text"/><div class="tag-list" id="experienceTags"></div></div>`
- **Line 588**: `<div class="form-group"><label for="summary">الملخص المهني</label><textarea dir="auto" id="summary" placeholder="ملخص مهني قصير..." style="min-height:90px;"></textarea></div>`
- **Line 594**: `<div class="form-group"><label for="targetCompany">{{ _('Target Company') }}</label><input dir="auto" id="targetCompany" placeholder="Murex, Cisco, Bank Audi..." type="text"/></div>`
- **Line 595**: `<div class="form-group"><label for="targetJobTitle">{{ _('Target Job Title') }}</label><input dir="auto" id="targetJobTitle" placeholder="Senior Network Engineer" type="text"/></div>`
- **Line 610**: `<div class="form-group"><label for="targetTitles">{{ _('Target Job Titles') }}</label><input dir="auto" id="targetTitles" placeholder="Senior Network Engineer, IT Manager..." type="text"/></div>`
- **Line 611**: `<div class="form-group"><label for="targetLocations">{{ _('Target Locations') }}</label><input dir="auto" id="targetLocations" placeholder="Dubai, Remote, Riyadh, Beirut..." type="text"/></div>`

#### 2. Visual Theme & Style
- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.
- ❌ **Glassmorphism Card Style**: Not explicitly detected via classes (`backdrop-blur`, `bg-white/`, `glass`).

#### 3. Button/Link Hover Interactions
- ❌ 12 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 552**: `<button class="btn btn-ai pulse-btn" id="parseBtn" onclick="parseCV()" style="width:100%;padding:18px;font-size:18px;" type="button">` (missing transform, missing shadow)
  - **Line 702**: `<button class="btn btn-ai" onclick="previewEmail()" type="button">` (missing transform, missing shadow)
  - **Line 703**: `<button class="btn btn-sm btn-outline" onclick="regenerateAll()" type="button">` (missing transform, missing shadow)
  - **Line 720**: `<button class="btn pulse-btn" onclick="saveAndGoCampaign()" style="padding:16px 32px;font-size:18px;background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;" type="button">` (missing transform, missing shadow)
  - **Line 723**: `<button class="btn btn-outline" onclick="downloadCV()" style="padding:16px 28px;font-size:15px;" type="button">` (missing transform, missing shadow)
  - **Line 726**: `<button class="btn btn-sm btn-outline" onclick="saveProfile()" style="font-size:14px;" type="button">` (missing transform, missing shadow)
  - **Line 738**: `<button class="modal-close" onclick="closePreview()">` (missing transform, missing shadow)
  - **Line 741**: `<button class="preview-tab active" onclick="switchPreviewTab('email')">` (missing transform, missing shadow)
  - **Line 742**: `<button class="preview-tab" onclick="switchPreviewTab('cv')">` (missing transform, missing shadow)
  - **Line 743**: `<button class="preview-tab" onclick="switchPreviewTab('cl')">` (missing transform, missing shadow)
  - ... and 2 more buttons.

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', monospace, 'Cairo', 'Inter', sans-serif` | Classes: `None (inherits)`
- ✅ No font-size violations found (all Arabic content is >= 16px).
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `ats_scorer.html`

#### 1. Placeholder Text
The following placeholder texts/attributes were detected:
- **Line 21**: `<textarea class="w-full min-h-[300px] bg-slate-950/50 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 rounded-xl p-4 text-sm text-slate-200 font-mono resize-y outline-none transition-all custom-scrollbar" dir="auto" id="ats-resume" placeholder="Paste your full resume text here...`
- **Line 45**: `<input class="w-full bg-slate-950/50 border border-slate-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 rounded-lg ps-9 pe-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none transition-all" dir="auto" id="ats-url" placeholder="Or paste a job posting URL..." type="url"/>`
- **Line 51**: `<textarea class="w-full flex-1 min-h-[180px] bg-slate-950/50 border border-slate-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 rounded-xl p-4 text-sm text-slate-200 font-mono resize-y outline-none transition-all custom-scrollbar mb-4" dir="auto" id="ats-job-desc" placeholder="Paste the job description here...`
- **Line 65**: `<input class="w-full bg-slate-950/50 border border-slate-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 rounded-lg ps-9 pe-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none transition-all" dir="auto" id="ats-job-title" placeholder="Job title (optional, e.g. Senior Network Engineer)" type="text"/>`
- **Line 392**: `<input dir="auto" type="text" class="bulk-title w-full sm:w-1/3 bg-slate-950/50 border border-slate-700 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50 rounded-lg px-4 py-2 text-sm text-white placeholder-slate-500 outline-none transition-all" placeholder="Job Title (e.g. Developer)" />`
- **Line 393**: `<input dir="auto" type="text" class="bulk-desc w-full sm:flex-1 bg-slate-950/50 border border-slate-700 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50 rounded-lg px-4 py-2 text-sm text-white placeholder-slate-500 outline-none transition-all" placeholder="Paste JD or requirements..." />`

#### 2. Visual Theme & Style
- **Dark Gradient Background**: Detected. 
  - Classes: `['class="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-base font-black tracking-wide shadow-[0_0_20px_rgba(79,70,229,0.3)] transition-all flex items-center gap-3 border border-indigo-400/30"', 'class="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"', 'class="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"', 'class="absolute inset-0 bg-gradient-to-br from-yellow-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"']`
- **Glassmorphism Card Style**: Detected. 
  - Verified selectors/classes on lines: 17, 38, 82, 115, 141...

#### 3. Button/Link Hover Interactions
- ❌ 6 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 47**: `<button class="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 border border-slate-700 whitespace-nowrap" id="btn-url-import" onclick="importFromUrl()">` (has transform, missing shadow)
  - **Line 71**: `<button class="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-base font-black tracking-wide shadow-[0_0_20px_rgba(79,70,229,0.3)] transition-all flex items-center gap-3 border border-indigo-400/30" id="btn-score" onclick="scoreResume()">` (has transform, missing shadow)
  - **Line 74**: `<button class="px-5 py-3.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-bold transition-all flex items-center gap-2 border border-slate-700" id="btn-bulk-toggle" onclick="toggleBulkMode()">` (has transform, missing shadow)
  - **Line 90**: `<button class="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-bold tracking-wide shadow-[0_0_15px_rgba(147,51,234,0.3)] transition-all flex items-center gap-2 border border-purple-400/50" id="btn-bulk-score" onclick="scoreBulk()">` (has transform, missing shadow)
  - **Line 97**: `<button class="mt-4 px-4 py-2 border border-dashed border-slate-600 text-slate-400 hover:text-white hover:border-slate-400 hover:bg-slate-800/50 rounded-lg text-sm font-medium transition-all flex items-center gap-2 w-full justify-center" onclick="addBulkRow()">` (has transform, missing shadow)
  - **Line 394**: `<button onclick="this.closest('.bulk-job-row').remove()" class="p-2 bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-slate-700 hover:border-red-500/30 rounded-lg transition-colors flex-shrink-0">` (has transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `None (inherits)` | Classes: `None (inherits)`
- ✅ No font-size violations found (all Arabic content is >= 16px).
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `resume_tailor.html`

#### 1. Placeholder Text
The following placeholder texts/attributes were detected:
- **Line 51**: `.tailor-panel textarea::placeholder { color: #475569; font-style: italic; }`
- **Line 312**: `<textarea dir="auto" id="tailor-resume" placeholder="الصق نص سيرتك الذاتية بالكامل هنا...`
- **Line 324**: `<textarea dir="auto" id="tailor-job" placeholder="الصق الوصف الوظيفي الذي تريد التخصيص له...`
- **Line 334**: `<input dir="auto" id="tailor-job-title" placeholder="المسمى الوظيفي (اختياري، يساعد في سياق الذكاء الاصطناعي)" style="margin-top:10px;width:100%;padding:10px 14px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#e2e8f0;font-size:13px;font-family: 'Cairo', 'Inter',sans-serif;" type="text"/>`

#### 2. Visual Theme & Style
- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.
- ❌ **Glassmorphism Card Style**: Not explicitly detected via classes (`backdrop-blur`, `bg-white/`, `glass`).

#### 3. Button/Link Hover Interactions
- ❌ 5 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 346**: `<button class="btn btn-ai" id="btn-tailor" onclick="tailorResume()" style="font-size:16px;padding:13px 28px;">` (missing transform, missing shadow)
  - **Line 371**: `<button class="diff-toggle-btn active" id="toggle-tailored" onclick="switchView('tailored')">` (missing transform, missing shadow)
  - **Line 372**: `<button class="diff-toggle-btn" id="toggle-diff" onclick="switchView('diff')">` (missing transform, missing shadow)
  - **Line 390**: `<button class="btn btn-outline btn-sm" onclick="copyToClipboard()">` (missing transform, missing shadow)
  - **Line 391**: `<button class="btn btn-primary btn-sm" onclick="downloadAsPDF()">` (missing transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', 'Georgia', 'Times New Roman', serif, 'Cairo', 'Inter', monospace, 'Cairo', 'Inter',sans-serif, 'Cairo', 'Georgia', serif, 'Cairo', 'Inter', sans-serif` | Classes: `None (inherits)`
- ❌ **Font-Size Violations** (3 instances where font size < 16px on Arabic content):
  - **Line 334**: `<input dir="auto" id="tailor-job-title" placeholder="المسمى الوظيفي (اختياري، يساعد في سياق الذكاء الاصطناعي)" style="margin-top:10px;width:100%;padding:10px 14px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#e2e8f0;font-size:13px;font-family: 'Cairo', 'Inter',sans-serif;" type="text"/>`
  - **Line 349**: `<span style="color:#64748b;font-size:12px;">⚡ تخصيص مدعوم بالذكاء الاصطناعي — يستغرق حوالي 10 ثوانٍ</span>`
  - **Line 356**: `<div style="color:#94a3b8;font-size:14px;">يقوم الذكاء الاصطناعي بتخصيص سيرتك الذاتية... مطابقة الكلمات المفتاحية، تحسين النقاط...</div>`
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `wallet.html`

#### 1. Placeholder Text
The following placeholder texts/attributes were detected:
- **Line 59**: `.invoice-modal .qr-placeholder { width:120px; height:120px; margin:0 auto 16px; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:48px; }`
- **Line 93**: `.redeem-input::placeholder { color:#475569; font-family: 'Cairo', sans-serif;  }`
- **Line 196**: `<div class="qr-placeholder">🏦</div>`
- **Line 233**: `<input autocomplete="off" class="redeem-input" dir="auto" name="code" placeholder="XXXX-XXXX-XXXX" required="" type="text"/>`

#### 2. Visual Theme & Style
- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.
- ❌ **Glassmorphism Card Style**: Not explicitly detected via classes (`backdrop-blur`, `bg-white/`, `glass`).

#### 3. Button/Link Hover Interactions
- ❌ 20 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 110**: `<a class="btn-wallet primary" href="/pricing">` (missing transform, missing shadow)
  - **Line 111**: `<button class="btn-wallet" onclick="navigator.clipboard.writeText('{{ user_email }}');this.innerHTML='✅ تم النسخ!'">` (missing transform, missing shadow)
  - **Line 137**: `<button class="btn-wallet" id="toggleKeyBtn" onclick="toggleApiKey()" style="padding:2px 8px;font-size:11px;min-height:24px;line-height:1;">` (missing transform, missing shadow)
  - **Line 142**: `<button class="btn-wallet" onclick="navigator.clipboard.writeText('{{ user.api_key }}');this.innerHTML='✅ تم النسخ!';setTimeout(()=>` (missing transform, missing shadow)
  - **Line 144**: `<button class="btn-wallet" style="color:#f59e0b;border-color:rgba(245,158,11,.2);background:rgba(245,158,11,.08);" type="submit">` (missing transform, missing shadow)
  - **Line 167**: `<button class="preset-btn" data-amount="10">` (missing transform, missing shadow)
  - **Line 168**: `<button class="preset-btn selected" data-amount="25">` (missing transform, missing shadow)
  - **Line 169**: `<button class="preset-btn" data-amount="50">` (missing transform, missing shadow)
  - **Line 170**: `<button class="preset-btn" data-amount="100">` (missing transform, missing shadow)
  - **Line 180**: `<button class="coin-btn selected" data-coin="USDT">` (missing transform, missing shadow)
  - ... and 10 more buttons.

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', monospace, 'Cairo', sans-serif` | Classes: `None (inherits)`
- ❌ **Font-Size Violations** (5 instances where font size < 16px on Arabic content):
  - **Line 134**: `<div style="font-size:12px;text-transform:uppercase;color:#64748b;margin-bottom:2px;">{{ _('مفتاح API الخاص بك') }}</div>`
  - **Line 137**: `<button class="btn-wallet" id="toggleKeyBtn" onclick="toggleApiKey()" style="padding:2px 8px;font-size:11px;min-height:24px;line-height:1;">👁️ عرض</button>`
  - **Line 178**: `<label style="font-size:11px;color:#64748b;text-transform:uppercase;">ادفع بـ</label>`
  - **Line 199**: `<p style="font-size:11px;color:#64748b;margin-bottom:16px;">الطلب: <span id="invOrder">---</span></p>`
  - **Line 219**: `<button class="btn" onclick="navigator.clipboard.writeText('{{ addr }}');this.innerHTML='✅ تم النسخ!';setTimeout(()=>this.innerHTML='📋 نسخ',2000)" style="margin-top:8px;padding:6px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.03);color:#94a3b8;cursor:pointer;font-size:11px;">📋 نسخ</button>`
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `war_room.html`

#### 1. Placeholder Text
- ✅ No placeholder texts or standard 'TODO'/'Lorem Ipsum' markers were found.

#### 2. Visual Theme & Style
- **Dark Gradient Background**: Detected. 
  - Classes: `['class="h-full bg-gradient-to-r from-green-500 via-cyan-400 to-blue-500 transition-all duration-1000"', 'class="h-full rounded-full transition-all duration-500 {{ \'bg-gradient-to-r from-red-500 to-orange-500\' if c.heat_cls == \'hot\' else \'bg-gradient-to-r from-amber-500 to-lime-400\' if c.heat_cls == \'good\' else \'bg-gradient-to-r from-cyan-500 to-blue-500\' }}"']`
- **Glassmorphism Card Style**: Detected. 
  - Verified selectors/classes on lines: 12, 32, 36, 40, 44...

#### 3. Button/Link Hover Interactions
- ❌ 4 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 132**: `<button class="bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2" onclick="copyText(this)">` (has transform, missing shadow)
  - **Line 159**: `<button class="bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2" onclick="copyGuide(this)">` (has transform, missing shadow)
  - **Line 191**: `<button class="bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2" onclick="copyHtml(this)">` (has transform, missing shadow)
  - **Line 194**: `<button class="bg-slate-800 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-slate-700 hover:text-white transition-all flex items-center gap-2" onclick="generateInterviewPrep({{ cv.id }}, this)">` (has transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `None (inherits)` | Classes: `None (inherits)`
- ❌ **Font-Size Violations** (10 instances where font size < 16px on Arabic content):
  - **Line 59**: `<h3 class="text-sm font-bold text-green-400 font-mono tracking-wider mb-4 before:content-['[_'] before:text-green-500/40 after:content-['_]'] after:text-green-500/40">تقرير استخباراتي - الرواتب</h3>`
  - **Line 95**: `<h3 class="text-sm font-bold text-green-400 font-mono tracking-wider mb-4 before:content-['[_'] before:text-green-500/40 after:content-['_]'] after:text-green-500/40">رادار المنافسة</h3>`
  - **Line 114**: `<div class="text-xs font-mono">[ لا توجد بيانات منافسة بعد — يتفعل الرادار عند تنفيذ الحملة ]</div>`
  - **Line 120**: `<h3 class="text-sm font-bold text-green-400 font-mono tracking-wider mb-4 before:content-['[_'] before:text-green-500/40 after:content-['_]'] after:text-green-500/40">محطة حرب لينكدإن</h3>`
  - **Line 141**: `<div class="text-xs font-mono">[ اشترِ صاروخ التواصل لتوليد رسائل طلب تواصل تلقائية ]</div>`
  - ... and 5 more size violations.
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ❌ **Letter-Spacing Violations** (12 instances where letter-spacing/tracking classes are used on Arabic text):
  - **Line 34**: `<div class="text-[10px] text-slate-500 uppercase tracking-widest mt-1">[ الأهداف ]</div>`
  - **Line 38**: `<div class="text-[10px] text-slate-500 uppercase tracking-widest mt-1">[ مُرسل ]</div>`
  - **Line 42**: `<div class="text-[10px] text-slate-500 uppercase tracking-widest mt-1">[ فُتح ]</div>`
  - **Line 46**: `<div class="text-[10px] text-slate-500 uppercase tracking-widest mt-1">[ ردود ]</div>`
  - **Line 50**: `<div class="text-[10px] text-slate-500 uppercase tracking-widest mt-1">[ فشل ]</div>`
  - **Line 54**: `<div class="text-[10px] text-slate-500 uppercase tracking-widest mt-1">[ متابعات ]</div>`
  - **Line 59**: `<h3 class="text-sm font-bold text-green-400 font-mono tracking-wider mb-4 before:content-['[_'] before:text-green-500/40 after:content-['_]'] after:text-green-500/40">تقرير استخباراتي - الرواتب</h3>`
  - **Line 95**: `<h3 class="text-sm font-bold text-green-400 font-mono tracking-wider mb-4 before:content-['[_'] before:text-green-500/40 after:content-['_]'] after:text-green-500/40">رادار المنافسة</h3>`
  - **Line 120**: `<h3 class="text-sm font-bold text-green-400 font-mono tracking-wider mb-4 before:content-['[_'] before:text-green-500/40 after:content-['_]'] after:text-green-500/40">محطة حرب لينكدإن</h3>`
  - **Line 147**: `<h3 class="text-sm font-bold text-green-400 font-mono tracking-wider mb-4 before:content-['[_'] before:text-green-500/40 after:content-['_]'] after:text-green-500/40">ترسانة تحضير المقابلات</h3>`
  - ... and 2 more letter-spacing violations.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---

### `battle_station.html`

#### 1. Placeholder Text
- ✅ No placeholder texts or standard 'TODO'/'Lorem Ipsum' markers were found.

#### 2. Visual Theme & Style
- ❌ **Dark Gradient Background**: Not explicitly declared in body classes or standard variables.
- ❌ **Glassmorphism Card Style**: Not explicitly detected via classes (`backdrop-blur`, `bg-white/`, `glass`).

#### 3. Button/Link Hover Interactions
- ❌ 9 buttons/links are missing both `hover:transform` (hover:scale/hover:-translate-y) and `hover:box-shadow`:
  - **Line 246**: `<button class="bs-btn green" onclick="bsStartAll()">` (missing transform, missing shadow)
  - **Line 247**: `<button class="bs-btn red" onclick="bsStopAll()">` (missing transform, missing shadow)
  - **Line 248**: `<button class="bs-btn green" onclick="forceScanNow()" style="background: linear-gradient(135deg, #10b981, #059669); border-color: rgba(16,185,129,.3);">` (missing transform, missing shadow)
  - **Line 249**: `<a class="bs-btn amber" href="/new-campaign">` (missing transform, missing shadow)
  - **Line 250**: `<a class="bs-btn" href="/sent-emails">` (missing transform, missing shadow)
  - **Line 256**: `<a class="bs-cta-btn" href="/new-campaign">` (missing transform, missing shadow)
  - **Line 313**: `<a class="bs-btn bs-btn-sm" href="/campaign/{{ c['campaign_id'] }}/war-room" style="margin-inline-start:auto;">` (missing transform, missing shadow)
  - **Line 321**: `<a class="bs-cta-btn" href="/new-campaign">` (missing transform, missing shadow)
  - **Line 393**: `<a class="bs-cta-btn" href="/new-campaign">` (missing transform, missing shadow)

#### 4. Arabic Typography (Cairo/Tajawal, min 16px, line-height 1.6-2.0, no letter-spacing)
- **Font Families**: Styles: `'Cairo', monospace, 'Cairo', 'Inter', sans-serif` | Classes: `None (inherits)`
- ❌ **Font-Size Violations** (2 instances where font size < 16px on Arabic content):
  - **Line 203**: `<div style="font-size: 9px; color: #60a5fa; font-weight: 800;  text-transform: uppercase; margin-bottom: 2px;">الفحص التلقائي التالي</div>`
  - **Line 205**: `<div id="autopilot-status" style="font-size: 10px; color: #94a3b8; font-weight: 600; margin-top: 4px;">جاري تهيئة نظام التقديم التلقائي...</div>`
- ✅ No line-height violations found (all Arabic content has line-height between 1.6 and 2.0).
- ✅ No letter-spacing/tracking classes detected on Arabic text elements.

#### 5. Form Inputs `dir="auto"` Alignment
- ✅ All inputs, textareas, and selects correctly define `dir="auto"`.

#### 6. Layout Properties (Logical CSS vs Physical Layout)
- ✅ No physical properties (like margin-left, padding-right) or physical Tailwind classes (ml-, pr-) were detected in layout elements.

---
