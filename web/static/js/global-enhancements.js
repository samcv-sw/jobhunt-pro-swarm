/**
 * GLOBAL ENHANCEMENTS JS — JobHunt Pro World-Class Suite
 * Silicon Valley Conversion Toasts, Chinese Zero-Latency UX, & Global Command Palette
 */

(function () {
  'use strict';

  // --- 1. SILICON VALLEY LIVE CONVERSION TOASTS ---
  const TOAST_EVENTS = [
    { title: '⚡ ATS Optimizer Boost', desc: 'Candidate in Riyadh updated resume match score to 98%' },
    { title: '🤖 Auto-Applier Swarm', desc: '14 applications submitted auto-pilot in Dubai' },
    { title: '🎯 Recruiter Match', desc: 'Executive candidate matched with Saudi Aramco hiring lead' },
    { title: '💼 Live Interview Copilot', desc: 'Candidate passed final tech round in Abu Dhabi' },
    { title: '🚀 Salary Negotiator', desc: 'Offer counter-proposal generated +18% package increase' }
  ];

  function createToastContainer() {
    let container = document.getElementById('live-conversion-toasts');
    if (!container) {
      container = document.createElement('div');
      container.id = 'live-conversion-toasts';
      document.body.appendChild(container);
    }
    return container;
  }

  function showConversionToast(data) {
    const container = createToastContainer();
    const toast = document.createElement('div');
    toast.className = 'conversion-toast';
    
    // Auto-detect dir
    const isRtl = document.documentElement.getAttribute('dir') === 'rtl';

    toast.innerHTML = `
      <div class="toast-icon">✨</div>
      <div class="toast-content">
        <div class="toast-title">${data.title}</div>
        <div class="toast-desc">${data.desc}</div>
      </div>
      <button class="toast-close" aria-label="Close">&times;</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.classList.add('toast-hiding');
      setTimeout(() => toast.remove(), 300);
    });

    container.appendChild(toast);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.classList.add('toast-hiding');
        setTimeout(() => toast.remove(), 300);
      }
    }, 5500);
  }

  function scheduleRandomToasts() {
    // Show first toast after 4s, then every 25s
    setTimeout(() => {
      const initial = TOAST_EVENTS[Math.floor(Math.random() * TOAST_EVENTS.length)];
      showConversionToast(initial);
      
      setInterval(() => {
        const item = TOAST_EVENTS[Math.floor(Math.random() * TOAST_EVENTS.length)];
        showConversionToast(item);
      }, 25000);
    }, 4000);
  }

  // --- 2. COMMAND PALETTE (CMD + K / CTRL + K) ---
  function initCommandPalette() {
    const backdrop = document.createElement('div');
    backdrop.id = 'global-cmd-k-backdrop';
    
    const isRtl = document.documentElement.getAttribute('dir') === 'rtl';
    const searchPlaceholder = isRtl ? 'ابحث عن أي قسم أو أداة... (Esc للإغلاق)' : 'Search commands, tools, dashboards... (Esc to close)';

    backdrop.innerHTML = `
      <div class="cmd-k-dialog">
        <div class="cmd-k-input-wrapper">
          <span style="color:#38bdf8;">🔍</span>
          <input type="text" id="cmd-k-search-input" placeholder="${searchPlaceholder}" />
          <span class="cmd-k-shortcut">ESC</span>
        </div>
        <div class="cmd-k-results" id="cmd-k-results-list">
          <a href="/dashboard" class="cmd-k-item">
            <span>📊 ${isRtl ? 'لوحة التحكم الرئيسية' : 'Main Dashboard'}</span>
            <span class="cmd-k-shortcut">⌘D</span>
          </a>
          <a href="/ats/analyzer" class="cmd-k-item">
            <span>⚡ ${isRtl ? 'محلل ومطابق السيرة الذاتية (ATS)' : 'ATS Resume Analyzer'}</span>
            <span class="cmd-k-shortcut">⌘A</span>
          </a>
          <a href="/auto-applier" class="cmd-k-item">
            <span>🤖 ${isRtl ? 'سوارم التقديم التلقائي' : 'Auto-Applier Swarm'}</span>
            <span class="cmd-k-shortcut">⌘S</span>
          </a>
          <a href="/salary-negotiator" class="cmd-k-item">
            <span>💼 ${isRtl ? 'مفاوض الراتب الذكي' : 'AI Salary Negotiator'}</span>
            <span class="cmd-k-shortcut">⌘N</span>
          </a>
          <a href="/interview-prep" class="cmd-k-item">
            <span>🎙️ ${isRtl ? 'مساعد المقابلة المباشرة' : 'Live Interview Copilot'}</span>
            <span class="cmd-k-shortcut">⌘I</span>
          </a>
        </div>
      </div>
    `;

    document.body.appendChild(backdrop);

    const input = backdrop.querySelector('#cmd-k-search-input');
    const items = backdrop.querySelectorAll('.cmd-k-item');

    function toggleCmdK(show) {
      if (show) {
        backdrop.classList.add('cmd-active');
        input.value = '';
        input.focus();
        items.forEach(el => el.style.display = 'flex');
      } else {
        backdrop.classList.remove('cmd-active');
      }
    }

    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const isOpen = backdrop.classList.contains('cmd-active');
        toggleCmdK(!isOpen);
      } else if (e.key === 'Escape' && backdrop.classList.contains('cmd-active')) {
        toggleCmdK(false);
      }
    });

    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        toggleCmdK(false);
      }
    });

    input.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      items.forEach(item => {
        const text = item.innerText.toLowerCase();
        item.style.display = text.includes(q) ? 'flex' : 'none';
      });
    });
  }

  // --- 3. ZERO-LATENCY UNIVERSAL GLOBAL LOCALIZATION & TRANSLATION ENGINE ---
  function setCookie(name, value, days) {
    let expires = "";
    if (days) {
      let date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
    if (location.hostname && location.hostname.includes('.') && location.hostname !== '127.0.0.1' && location.hostname !== 'localhost') {
      let domainParts = location.hostname.split('.');
      if (domainParts.length >= 2) {
        let rootDomain = '.' + domainParts.slice(-2).join('.');
        document.cookie = name + "=" + (value || "") + expires + "; path=/; domain=" + rootDomain;
      }
    }
  }

  function clearCookie(name) {
    document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/";
    if (location.hostname && location.hostname.includes('.') && location.hostname !== '127.0.0.1' && location.hostname !== 'localhost') {
      let domainParts = location.hostname.split('.');
      if (domainParts.length >= 2) {
        let rootDomain = '.' + domainParts.slice(-2).join('.');
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=" + rootDomain;
      }
    }
  }

  window.switchGlobalLang = function(targetLang, e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!targetLang) return;

    const cleanCode = targetLang.split('-')[0].toLowerCase();

    if (cleanCode === 'ar' || cleanCode === 'en' || cleanCode === 'zh') {
      clearCookie('googtrans');
      setCookie('lang', cleanCode, 365);
      localStorage.setItem('jh_locale', cleanCode);
      window.location.href = '/lang/' + cleanCode;
      return;
    }

    setCookie('lang', targetLang, 365);
    localStorage.setItem('jh_locale', targetLang);
    setCookie('googtrans', '/auto/' + targetLang, 365);

    const isRtl = ['ar', 'fa', 'ur', 'he', 'ps', 'sd', 'yi'].includes(cleanCode);
    document.documentElement.setAttribute('lang', targetLang);
    document.documentElement.setAttribute('dir', isRtl ? 'rtl' : 'ltr');

    syncLangPickerUI(targetLang);

    const select = document.querySelector('#global-world-lang-select');
    if (select) {
      select.value = targetLang;
    }

    const gtCombo = document.querySelector('.goog-te-combo');
    if (gtCombo && gtCombo.options && gtCombo.options.length > 0) {
      let matchedOpt = Array.from(gtCombo.options).find(o => o.value.toLowerCase() === targetLang.toLowerCase() || o.value.toLowerCase() === cleanCode);
      if (matchedOpt) {
        gtCombo.value = matchedOpt.value;
        if (typeof gtCombo.onchange === 'function') gtCombo.onchange();
        gtCombo.dispatchEvent(new Event('change', { bubbles: true }));
        gtCombo.dispatchEvent(new Event('input', { bubbles: true }));
        return;
      }
    }

    const cleanUrl = window.location.href.split('?')[0].split('#')[0];
    window.location.href = cleanUrl + '?lang=' + targetLang;
  };

  const ALL_WORLD_LANGUAGES = [
    { code: 'ar', name: '🇦🇪 العربية (Arabic)' },
    { code: 'en', name: '🇬🇧 English' },
    { code: 'zh-CN', name: '🇨🇳 中文 (Simplified Chinese)' },
    { code: 'zh-TW', name: '🇹🇼 繁體中文 (Traditional Chinese)' },
    { code: 'fr', name: '🇫🇷 Français (French)' },
    { code: 'es', name: '🇪🇸 Español (Spanish)' },
    { code: 'de', name: '🇩🇪 Deutsch (German)' },
    { code: 'ja', name: '🇯🇵 日本語 (Japanese)' },
    { code: 'ru', name: '🇷🇺 Русский (Russian)' },
    { code: 'pt', name: '🇵🇹 Português (Portuguese)' },
    { code: 'it', name: '🇮🇹 Italiano (Italian)' },
    { code: 'tr', name: '🇹🇷 Türkçe (Turkish)' },
    { code: 'hi', name: '🇮🇳 हिन्दी (Hindi)' },
    { code: 'ko', name: '🇰🇷 한국어 (Korean)' },
    { code: 'nl', name: '🇳🇱 Nederlands (Dutch)' },
    { code: 'pl', name: '🇵🇱 Polski (Polish)' },
    { code: 'sv', name: '🇸🇪 Svenska (Swedish)' },
    { code: 'id', name: '🇮🇩 Bahasa Indonesia' },
    { code: 'vi', name: '🇻🇳 Tiếng Việt (Vietnamese)' },
    { code: 'fa', name: '🇮🇷 فارسی (Persian)' },
    { code: 'ur', name: '🇵🇰 اردو (Urdu)' },
    { code: 'af', name: '🇿🇦 Afrikaans' },
    { code: 'sq', name: '🇦🇱 Shqip (Albanian)' },
    { code: 'am', name: '🇪🇹 አማርኛ (Amharic)' },
    { code: 'hy', name: '🇦🇲 Հայերեն (Armenian)' },
    { code: 'as', name: '🇮🇳 অসমীয়া (Assamese)' },
    { code: 'ay', name: '🇧🇴 Aymar aru (Aymara)' },
    { code: 'az', name: '🇦🇿 Azərbaycan (Azerbaijani)' },
    { code: 'bm', name: '🇲🇱 Bamanankan (Bambara)' },
    { code: 'eu', name: '🇪🇸 Euskara (Basque)' },
    { code: 'be', name: '🇧🇾 Беларуская (Belarusian)' },
    { code: 'bn', name: '🇧🇩 বাংলা (Bengali)' },
    { code: 'bho', name: '🇮🇳 भोजपुरी (Bhojpuri)' },
    { code: 'bs', name: '🇧🇦 Bosanski (Bosnian)' },
    { code: 'bg', name: '🇧🇬 Български (Bulgarian)' },
    { code: 'ca', name: '🇪🇸 Català (Catalan)' },
    { code: 'ceb', name: '🇵🇭 Cebuano' },
    { code: 'ny', name: '🇲🇼 Nyanja (Chichewa)' },
    { code: 'co', name: '🇫🇷 Corsu (Corsican)' },
    { code: 'hr', name: '🇭🇷 Hrvatski (Croatian)' },
    { code: 'cs', name: '🇨🇿 Čeština (Czech)' },
    { code: 'da', name: '🇩🇰 Dansk (Danish)' },
    { code: 'dv', name: '🇲🇻 ދިވެހި (Dhivehi)' },
    { code: 'doi', name: '🇮🇳 डोगरी (Dogri)' },
    { code: 'eo', name: '🌐 Esperanto' },
    { code: 'et', name: '🇪🇪 Eesti (Estonian)' },
    { code: 'ee', name: '🇬🇭 Ɛwɛgbɛ (Ewe)' },
    { code: 'tl', name: '🇵🇭 Tagalog (Filipino)' },
    { code: 'fi', name: '🇫🇮 Suomi (Finnish)' },
    { code: 'fy', name: '🇳🇱 Frysk (Frisian)' },
    { code: 'gl', name: '🇪🇸 Galego (Galician)' },
    { code: 'ka', name: '🇬🇪 ქართული (Georgian)' },
    { code: 'el', name: '🇬🇷 Ελληνικά (Greek)' },
    { code: 'gn', name: '🇵🇾 Avañe\'ẽ (Guarani)' },
    { code: 'gu', name: '🇮🇳 ગુજરાતી (Gujarati)' },
    { code: 'ht', name: '🇭🇹 Kreyòl Ayisyen (Haitian)' },
    { code: 'ha', name: '🇳🇬 Hausa' },
    { code: 'haw', name: '🇺🇸 ʻŌlelo Hawaiʻi (Hawaiian)' },
    { code: 'iw', name: '🇮🇱 עברית (Hebrew)' },
    { code: 'hmn', name: '🇱🇦 Hmoob (Hmong)' },
    { code: 'hu', name: '🇭🇺 Magyar (Hungarian)' },
    { code: 'is', name: '🇮🇸 Íslenska (Icelandic)' },
    { code: 'ig', name: '🇳🇬 Asụsụ Igbo' },
    { code: 'ilo', name: '🇵🇭 Ilokano' },
    { code: 'ga', name: '🇮🇪 Gaeilge (Irish)' },
    { code: 'jw', name: '🇮🇩 Basa Jawa (Javanese)' },
    { code: 'kn', name: '🇮🇳 ಕನ್ನಡ (Kannada)' },
    { code: 'kk', name: '🇰🇿 Қазақ тілі (Kazakh)' },
    { code: 'km', name: '🇰🇭 ភាសាខ្មែរ (Khmer)' },
    { code: 'rw', name: '🇷🇼 Kinyarwanda' },
    { code: 'kri', name: '🇸🇱 Krio' },
    { code: 'ku', name: '🇮🇶 Kurdî (Kurdish)' },
    { code: 'ckb', name: '🇮🇶 کوردیی سۆرانی (Sorani)' },
    { code: 'ky', name: '🇰🇬 Кыргызча (Kyrgyz)' },
    { code: 'lo', name: '🇱🇦 ພາສາລາວ (Lao)' },
    { code: 'la', name: '🇻🇦 Latina (Latin)' },
    { code: 'lv', name: '🇱🇻 Latviešu (Latvian)' },
    { code: 'ln', name: '🇨🇩 Lingála' },
    { code: 'lt', name: '🇱🇹 Lietuvių (Lithuanian)' },
    { code: 'lg', name: '🇺🇬 Luganda' },
    { code: 'lb', name: '🇱🇺 Lëtzebuergesch (Luxembourgish)' },
    { code: 'mk', name: '🇲🇰 Македонски (Macedonian)' },
    { code: 'mai', name: '🇮🇳 मैथिली (Maithili)' },
    { code: 'mg', name: '🇲🇬 Malagasy' },
    { code: 'ms', name: '🇲🇾 Bahasa Melayu (Malay)' },
    { code: 'ml', name: '🇮🇳 മലയാളം (Malayalam)' },
    { code: 'mt', name: '🇲🇹 Malti (Maltese)' },
    { code: 'mi', name: '🇳ℤ Te Reo Māori' },
    { code: 'mr', name: '🇮🇳 Marathi' },
    { code: 'lus', name: '🇮🇳 Mizo' },
    { code: 'mn', name: '🇲🇳 Монгол (Mongolian)' },
    { code: 'my', name: '🇲🇲 မြန်မာစာ (Myanmar)' },
    { code: 'ne', name: '🇳🇵 नेपाली (Nepali)' },
    { code: 'no', name: '🇳🇴 Norsk (Norwegian)' },
    { code: 'om', name: '🇪🇹 Afaan Oromoo (Oromo)' },
    { code: 'ps', name: '🇦фом پښتو (Pashto)' },
    { code: 'pa', name: '🇮🇳 Punjabi' },
    { code: 'qu', name: '🇵🇪 Runasimi (Quechua)' },
    { code: 'ro', name: '🇷🇴 Română (Romanian)' },
    { code: 'sm', name: '🇼🇸 Gagana Samoa' },
    { code: 'sa', name: '🇮🇳 संस्कृतम् (Sanskrit)' },
    { code: 'gd', name: '🏴󠁧󠁢󠁳󠁣󠁴󠁿 Gàidhlig (Scots Gaelic)' },
    { code: 'nso', name: '🇿🇦 Sepedi' },
    { code: 'sr', name: '🇸🇷 Српски (Serbian)' },
    { code: 'st', name: '🇱🇸 Sesotho' },
    { code: 'sn', name: '🇿🇼 chiShona' },
    { code: 'sd', name: '🇵🇰 سنڌي (Sindhi)' },
    { code: 'si', name: '🇱🇰 සිංහල (Sinhala)' },
    { code: 'sk', name: '🇸🇰 Slovenčina (Slovak)' },
    { code: 'sl', name: '🇸🇮 Slovenščina (Slovenian)' },
    { code: 'so', name: '🇸🇴 Soomaali (Somali)' },
    { code: 'su', name: '🇮🇩 Basa Sunda (Sundanese)' },
    { code: 'sw', name: '🇰🇪 Kiswahili (Swahili)' },
    { code: 'tg', name: '🇹🇯 Тоҷикӣ (Tajik)' },
    { code: 'ta', name: '🇮🇳 தமிழ் (Tamil)' },
    { code: 'tt', name: '🇷🇺 Татар (Tatar)' },
    { code: 'te', name: '🇮🇳 తెలుగు (Telugu)' },
    { code: 'th', name: '🇹🇭 ไทย (Thai)' },
    { code: 'ti', name: '🇪🇹 ትግርኛ (Tigrinya)' },
    { code: 'ts', name: '🇿🇦 Xitsonga (Tsonga)' },
    { code: 'tk', name: '🇹🇲 Türkmen (Turkmen)' },
    { code: 'ak', name: '🇬🇭 Twi' },
    { code: 'uk', name: '🇺🇦 Українська (Ukrainian)' },
    { code: 'ug', name: '🇨🇳 ئۇيغۇرчә (Uyghur)' },
    { code: 'uz', name: '🇺🇿 O‘zbek (Uzbek)' },
    { code: 'cy', name: '🏴󠁧󠁢󠁷󠁬󠁳󠁿 Cymraeg (Welsh)' },
    { code: 'xh', name: '🇿🇦 isiXhosa' },
    { code: 'yi', name: '🇮🇱 ייִדיש (Yiddish)' },
    { code: 'yo', name: '🇳🇬 Yorùbá' },
    { code: 'zu', name: '🇿🇦 isiZulu' }
  ];

  window.toggleWorldLangMenu = function(e) {
    if (e && e.stopPropagation) e.stopPropagation();
    const btn = (e && e.currentTarget) ? e.currentTarget : document.querySelector('.world-lang-btn');
    const group = btn ? btn.closest('.lang-switcher-group') : null;
    const menu = group ? group.querySelector('.world-lang-menu') : document.querySelector('.world-lang-menu');
    if (!menu) return;

    const isOpen = menu.style.display === 'block';
    document.querySelectorAll('.world-lang-menu, .custom-lang-menu').forEach(m => m.style.display = 'none');
    menu.style.display = isOpen ? 'none' : 'block';

    if (!isOpen) {
      const list = menu.querySelector('.world-lang-list');
      const search = menu.querySelector('.world-lang-search');

      if (list && list.children.length === 0) {
        ALL_WORLD_LANGUAGES.forEach(item => {
          const row = document.createElement('div');
          row.style.cssText = 'display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:8px;font-size:12px;font-weight:600;color:#e2e8f0;cursor:pointer;transition:all 0.15s ease;';
          row.innerHTML = `<span>${item.name}</span>`;
          row.onmouseover = () => { row.style.background = 'rgba(0,240,255,0.15)'; row.style.color = '#00f0ff'; };
          row.onmouseout = () => { row.style.background = 'transparent'; row.style.color = '#e2e8f0'; };
          row.onclick = (ev) => {
            menu.style.display = 'none';
            if (window.switchGlobalLang) {
              window.switchGlobalLang(item.code, ev);
            }
          };
          list.appendChild(row);
        });
      }

      if (search) {
        search.value = '';
        if (window.filterWorldLangSearch) window.filterWorldLangSearch('');
        setTimeout(() => search.focus(), 50);
      }
    }
  };

  window.filterWorldLangSearch = function(query) {
    const list = document.querySelector('.world-lang-list');
    if (!list) return;
    const q = (query || '').toLowerCase();
    const rows = list.querySelectorAll('div');
    rows.forEach(r => {
      r.style.display = r.textContent.toLowerCase().includes(q) ? 'flex' : 'none';
    });
  };

  document.addEventListener('click', (e) => {
    const menu = document.querySelector('.world-lang-menu');
    const btn = document.querySelector('.world-lang-btn');
    if (menu && menu.style.display === 'block') {
      if (!menu.contains(e.target) && (!btn || !btn.contains(e.target))) {
        menu.style.display = 'none';
      }
    }
  });
    { code: 'ko', name: '🇰🇷 한국어 (Korean)' },
    { code: 'nl', name: '🇳🇱 Nederlands (Dutch)' },
    { code: 'pl', name: '🇵🇱 Polski (Polish)' },
    { code: 'sv', name: '🇸🇪 Svenska (Swedish)' },
    { code: 'id', name: '🇮🇩 Bahasa Indonesia' },
    { code: 'vi', name: '🇻🇳 Tiếng Việt (Vietnamese)' },
    { code: 'fa', name: '🇮🇷 فارسی (Persian)' },
    { code: 'ur', name: '🇵🇰 اردو (Urdu)' },
    { code: 'af', name: '🇿🇦 Afrikaans' },
    { code: 'sq', name: '🇦🇱 Shqip (Albanian)' },
    { code: 'am', name: '🇪🇹 አማርኛ (Amharic)' },
    { code: 'hy', name: '🇦🇲 Հայերեն (Armenian)' },
    { code: 'as', name: '🇮🇳 অসমীয়া (Assamese)' },
    { code: 'ay', name: '🇧🇴 Aymar aru (Aymara)' },
    { code: 'az', name: '🇦🇿 Azərbaycan (Azerbaijani)' },
    { code: 'bm', name: '🇲🇱 Bamanankan (Bambara)' },
    { code: 'eu', name: '🇪🇸 Euskara (Basque)' },
    { code: 'be', name: '🇧🇾 Беларуская (Belarusian)' },
    { code: 'bn', name: '🇧🇩 বাংলা (Bengali)' },
    { code: 'bho', name: '🇮🇳 भोजपुरी (Bhojpuri)' },
    { code: 'bs', name: '🇧🇦 Bosanski (Bosnian)' },
    { code: 'bg', name: '🇧🇬 Български (Bulgarian)' },
    { code: 'ca', name: '🇪🇸 Català (Catalan)' },
    { code: 'ceb', name: '🇵🇭 Cebuano' },
    { code: 'ny', name: '🇲🇼 Nyanja (Chichewa)' },
    { code: 'co', name: '🇫🇷 Corsu (Corsican)' },
    { code: 'hr', name: '🇭🇷 Hrvatski (Croatian)' },
    { code: 'cs', name: '🇨🇿 Čeština (Czech)' },
    { code: 'da', name: '🇩🇰 Dansk (Danish)' },
    { code: 'dv', name: '🇲🇻 ދިވެހި (Dhivehi)' },
    { code: 'doi', name: '🇮🇳 डोगरी (Dogri)' },
    { code: 'eo', name: '🌐 Esperanto' },
    { code: 'et', name: '🇪🇪 Eesti (Estonian)' },
    { code: 'ee', name: '🇬🇭 Ɛwɛgbɛ (Ewe)' },
    { code: 'tl', name: '🇵🇭 Tagalog (Filipino)' },
    { code: 'fi', name: '🇫🇮 Suomi (Finnish)' },
    { code: 'fy', name: '🇳🇱 Frysk (Frisian)' },
    { code: 'gl', name: '🇪🇸 Galego (Galician)' },
    { code: 'ka', name: '🇬🇪 ქართული (Georgian)' },
    { code: 'el', name: '🇬🇷 Ελληνικά (Greek)' },
    { code: 'gn', name: '🇵🇾 Avañe\'ẽ (Guarani)' },
    { code: 'gu', name: '🇮🇳 ગુજરાતી (Gujarati)' },
    { code: 'ht', name: '🇭🇹 Kreyòl Ayisyen (Haitian)' },
    { code: 'ha', name: '🇳🇬 Hausa' },
    { code: 'haw', name: '🇺🇸 ʻŌlelo Hawaiʻi (Hawaiian)' },
    { code: 'iw', name: '🇮🇱 עברית (Hebrew)' },
    { code: 'hmn', name: '🇱🇦 Hmoob (Hmong)' },
    { code: 'hu', name: '🇭🇺 Magyar (Hungarian)' },
    { code: 'is', name: '🇮🇸 Íslenska (Icelandic)' },
    { code: 'ig', name: '🇳🇬 Asụsụ Igbo' },
    { code: 'ilo', name: '🇵🇭 Ilokano' },
    { code: 'ga', name: '🇮🇪 Gaeilge (Irish)' },
    { code: 'jw', name: '🇮🇩 Basa Jawa (Javanese)' },
    { code: 'kn', name: '🇮🇳 ಕನ್ನಡ (Kannada)' },
    { code: 'kk', name: '🇰🇿 Қазақ тілі (Kazakh)' },
    { code: 'km', name: '🇰🇭 ភាសាខ្មែរ (Khmer)' },
    { code: 'rw', name: '🇷🇼 Kinyarwanda' },
    { code: 'kri', name: '🇸🇱 Krio' },
    { code: 'ku', name: '🇮🇶 Kurdî (Kurdish)' },
    { code: 'ckb', name: '🇮🇶 کوردیی سۆرانی (Sorani)' },
    { code: 'ky', name: '🇰🇬 Кыргызча (Kyrgyz)' },
    { code: 'lo', name: '🇱🇦 ພາສາລາວ (Lao)' },
    { code: 'la', name: '🇻🇦 Latina (Latin)' },
    { code: 'lv', name: '🇱🇻 Latviešu (Latvian)' },
    { code: 'ln', name: '🇨🇩 Lingála' },
    { code: 'lt', name: '🇱🇹 Lietuvių (Lithuanian)' },
    { code: 'lg', name: '🇺🇬 Luganda' },
    { code: 'lb', name: '🇱🇺 Lëtzebuergesch (Luxembourgish)' },
    { code: 'mk', name: '🇲🇰 Македонски (Macedonian)' },
    { code: 'mai', name: '🇮🇳 मैथिली (Maithili)' },
    { code: 'mg', name: '🇲🇬 Malagasy' },
    { code: 'ms', name: '🇲🇾 Bahasa Melayu (Malay)' },
    { code: 'ml', name: '🇮🇳 മലയാളം (Malayalam)' },
    { code: 'mt', name: '🇲🇹 Malti (Maltese)' },
    { code: 'mi', name: '🇳ℤ Te Reo Māori' },
    { code: 'mr', name: '🇮🇳 मराठी (Marathi)' },
    { code: 'lus', name: '🇮🇳 Mizo' },
    { code: 'mn', name: '🇲🇳 Монгол (Mongolian)' },
    { code: 'my', name: '🇲🇲 မြန်မာစာ (Myanmar)' },
    { code: 'ne', name: '🇳🇵 नेपाली (Nepali)' },
    { code: 'no', name: '🇳🇴 Norsk (Norwegian)' },
    { code: 'om', name: '🇪🇹 Afaan Oromoo (Oromo)' },
    { code: 'ps', name: '🇦🇫 پښتو (Pashto)' },
    { code: 'pa', name: '🇮🇳 Punjabi' },
    { code: 'qu', name: '🇵🇪 Runasimi (Quechua)' },
    { code: 'ro', name: '🇷🇴 Română (Romanian)' },
    { code: 'sm', name: '🇼🇸 Gagana Samoa' },
    { code: 'sa', name: '🇮🇳 संस्कृतम् (Sanskrit)' },
    { code: 'gd', name: '🏴󠁧󠁢󠁳󠁣󠁴󠁿 Gàidhlig (Scots Gaelic)' },
    { code: 'nso', name: '🇿🇦 Sepedi' },
    { code: 'sr', name: '🇸🇷 Српски (Serbian)' },
    { code: 'st', name: '🇱🇸 Sesotho' },
    { code: 'sn', name: '🇿🇼 chiShona' },
    { code: 'sd', name: '🇵🇰 سنڌي (Sindhi)' },
    { code: 'si', name: '🇱🇰 සිංહල (Sinhala)' },
    { code: 'sk', name: '🇸🇰 Slovenčina (Slovak)' },
    { code: 'sl', name: '🇸🇮 Slovenščina (Slovenian)' },
    { code: 'so', name: '🇸🇴 Soomaali (Somali)' },
    { code: 'su', name: '🇮🇩 Basa Sunda (Sundanese)' },
    { code: 'sw', name: '🇰🇪 Kiswahili (Swahili)' },
    { code: 'tg', name: '🇹🇯 Тоҷикӣ (Tajik)' },
    { code: 'ta', name: '🇮🇳 தமிழ் (Tamil)' },
    { code: 'tt', name: '🇷🇺 Татар (Tatar)' },
    { code: 'te', name: '🇮🇳 తెలుగు (Telugu)' },
    { code: 'th', name: '🇹🇭 ไทย (Thai)' },
    { code: 'ti', name: '🇪🇹 ትግርኛ (Tigrinya)' },
    { code: 'ts', name: '🇿🇦 Xitsonga (Tsonga)' },
    { code: 'tk', name: '🇹🇲 Türkmen (Turkmen)' },
    { code: 'ak', name: '🇬🇭 Twi' },
    { code: 'uk', name: '🇺🇦 Українська (Ukrainian)' },
    { code: 'ug', name: '🇨🇳 ئۇيغۇرчә (Uyghur)' },
    { code: 'uz', name: '🇺🇿 O‘zbek (Uzbek)' },
    { code: 'cy', name: '🏴󠁧󠁢󠁷󠁬󠁳󠁿 Cymraeg (Welsh)' },
    { code: 'xh', name: '🇿🇦 isiXhosa' },
    { code: 'yi', name: '🇮🇱 ייִדיש (Yiddish)' },
    { code: 'yo', name: '🇳🇬 Yorùbá' },
    { code: 'zu', name: '🇿🇦 isiZulu' }
  ];

  function syncLangPickerUI(activeLang) {
    if (!activeLang) return;
    const cleanCode = activeLang.split('-')[0].toLowerCase();
    const item = ALL_WORLD_LANGUAGES.find(o => o.code.toLowerCase() === activeLang.toLowerCase() || o.code.toLowerCase() === cleanCode) || ALL_WORLD_LANGUAGES[0];
    
    document.querySelectorAll('.custom-lang-picker-wrapper').forEach(wrapper => {
      const btn = wrapper.querySelector('.custom-lang-btn');
      if (btn) {
        const parts = item.name.split(' ');
        const flag = parts[0] || '🌐';
        const label = parts.slice(1).join(' ') || item.name;
        btn.querySelector('.lang-flag').textContent = flag;
        btn.querySelector('.lang-label').textContent = label;
      }
      const items = wrapper.querySelectorAll('.lang-item');
      items.forEach(el => {
        if (el.dataset.code.toLowerCase() === activeLang.toLowerCase() || el.dataset.code.toLowerCase() === cleanCode) {
          el.dataset.active = 'true';
          el.style.background = 'rgba(0,240,255,0.2)';
          el.style.color = '#00f0ff';
          el.style.fontWeight = '700';
        } else {
          el.dataset.active = 'false';
          el.style.background = 'transparent';
          el.style.color = '#e2e8f0';
          el.style.fontWeight = '600';
        }
      });
    });
  }

  function populateWorldLanguageDropdowns() {
    try {
      const dropdowns = document.querySelectorAll('#global-world-lang-select');
      dropdowns.forEach(select => {
        if (!select) return;
        if (select.children.length < 25) {
          select.innerHTML = '<option value="" disabled selected>🌐 More Languages...</option>';
          ALL_WORLD_LANGUAGES.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.code;
            opt.textContent = item.name;
            select.appendChild(opt);
          });
        }

        if (select.dataset.customized === 'true') return;
        select.dataset.customized = 'true';
        select.style.display = 'none'; // Hide raw select

        // Create Custom Glassmorphism Language Picker Wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'custom-lang-picker-wrapper';
        wrapper.style.cssText = 'position:relative;display:inline-block;margin-inline-start:4px;flex-shrink:0;z-index:9999;';

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'custom-lang-btn';
        btn.style.cssText = 'display:flex;align-items:center;gap:6px;background:rgba(15,23,42,0.85);color:#00f0ff;border:1px solid rgba(0,240,255,0.35);border-radius:10px;padding:4px 10px;font-size:12px;font-weight:700;cursor:pointer;backdrop-filter:blur(12px);transition:all 0.25s ease;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-family:inherit;';
        btn.innerHTML = `<span class="lang-flag" style="font-size:14px;">🌐</span><span class="lang-label" style="max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">Select Language</span><span class="lang-arrow" style="font-size:10px;color:#94a3b8;transition:transform 0.25s ease;">▼</span>`;

        btn.onmouseover = () => { btn.style.borderColor = 'rgba(0,240,255,0.7)'; btn.style.boxShadow = '0 0 14px rgba(0,240,255,0.35)'; };
        btn.onmouseout = () => { btn.style.borderColor = 'rgba(0,240,255,0.35)'; btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)'; };

        const menu = document.createElement('div');
        menu.className = 'custom-lang-menu';
        menu.style.cssText = 'display:none;position:absolute;top:calc(100% + 6px);inset-inline-end:0;width:250px;max-height:350px;background:rgba(10,15,30,0.96);border:1px solid rgba(0,240,255,0.3);border-radius:14px;box-shadow:0 14px 36px rgba(0,0,0,0.85), 0 0 20px rgba(0,240,255,0.18);backdrop-filter:blur(18px);overflow:hidden;z-index:10000;box-sizing:border-box;';

        menu.innerHTML = `
          <div style="padding:8px 10px;border-bottom:1px solid rgba(255,255,255,0.08);background:rgba(0,0,0,0.4);">
            <input type="text" class="lang-search" placeholder="🔍 Search language..." style="width:100%;box-sizing:border-box;background:rgba(255,255,255,0.06);color:#fff;border:1px solid rgba(0,240,255,0.25);border-radius:8px;padding:6px 10px;font-size:11px;outline:none;" />
          </div>
          <div class="lang-items-container" style="max-height:280px;overflow-y:auto;padding:4px;">
          </div>
        `;

        const itemsContainer = menu.querySelector('.lang-items-container');
        const searchInput = menu.querySelector('.lang-search');

        // Populate language items
        ALL_WORLD_LANGUAGES.forEach(item => {
          const row = document.createElement('div');
          row.className = 'lang-item';
          row.dataset.code = item.code;
          row.style.cssText = 'display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:8px;font-size:12px;font-weight:600;color:#e2e8f0;cursor:pointer;transition:all 0.15s ease;';
          row.innerHTML = `<span>${item.name}</span>`;
          
          row.onmouseover = () => { 
            if (row.dataset.active !== 'true') {
              row.style.background = 'rgba(0,240,255,0.15)'; 
              row.style.color = '#00f0ff'; 
            }
          };
          row.onmouseout = () => { 
            if (row.dataset.active !== 'true') {
              row.style.background = 'transparent'; 
              row.style.color = '#e2e8f0'; 
            }
          };

          row.onclick = (e) => {
            select.value = item.code;
            menu.style.display = 'none';
            btn.querySelector('.lang-arrow').style.transform = 'rotate(0deg)';
            if (window.switchGlobalLang) {
              window.switchGlobalLang(item.code, e);
            }
          };

          itemsContainer.appendChild(row);
        });

        // Search filter
        searchInput.oninput = (e) => {
          const q = e.target.value.toLowerCase();
          const items = itemsContainer.querySelectorAll('.lang-item');
          items.forEach(el => {
            el.style.display = el.textContent.toLowerCase().includes(q) ? 'flex' : 'none';
          });
        };

        // Toggle menu
        btn.onclick = (e) => {
          e.stopPropagation();
          const isOpen = menu.style.display === 'block';
          document.querySelectorAll('.custom-lang-menu').forEach(m => m.style.display = 'none');
          menu.style.display = isOpen ? 'none' : 'block';
          btn.querySelector('.lang-arrow').style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
          if (!isOpen) {
            searchInput.value = '';
            searchInput.oninput({ target: searchInput });
            setTimeout(() => searchInput.focus(), 50);
          }
        };

        // Close on outside click
        document.addEventListener('click', (e) => {
          if (!wrapper.contains(e.target)) {
            menu.style.display = 'none';
            btn.querySelector('.lang-arrow').style.transform = 'rotate(0deg)';
          }
        });

        if (select.parentNode) {
          select.parentNode.insertBefore(wrapper, select.nextSibling);
        }
      });
    } catch(e) {
      console.debug('Lang picker customization error:', e);
    }
  }

  function initGlobalTranslationEngine() {
    populateWorldLanguageDropdowns();

    const localLang = localStorage.getItem('jh_locale');
    const cookieMatch = document.cookie.match(/(?:^|;\s*)lang=([^;]+)/);
    const cookieLang = cookieMatch ? cookieMatch[1] : null;
    const urlParams = new URLSearchParams(window.location.search);
    const urlLang = urlParams.get('lang');
    const docLang = (document.documentElement.getAttribute('lang') || '').toLowerCase();
    
    // Priority: localLang -> cookieLang -> urlLang -> docLang -> 'ar'
    let activeLang = localLang || cookieLang || urlLang || (docLang && docLang !== 'ar' && docLang !== 'en' ? docLang : 'ar');
    activeLang = activeLang.toLowerCase();
    const cleanCode = activeLang.split('-')[0].toLowerCase();

    // Sync custom lang picker UI state
    syncLangPickerUI(activeLang);

    // Sync select dropdown UI state
    const dropdowns = document.querySelectorAll('#global-world-lang-select');
    dropdowns.forEach(select => {
      if (select) {
        let opt = Array.from(select.options).find(o => o.value.toLowerCase() === activeLang.toLowerCase() || o.value.toLowerCase() === cleanCode);
        if (opt) select.value = opt.value;
      }
    });

    if (cleanCode === 'ar' || cleanCode === 'en' || cleanCode === 'zh') {
      clearCookie('googtrans');
      return;
    }

    const isRtlLang = ['ar', 'fa', 'ur', 'he', 'ps', 'sd', 'yi'].includes(cleanCode);
    document.documentElement.setAttribute('lang', activeLang);
    document.documentElement.setAttribute('dir', isRtlLang ? 'rtl' : 'ltr');

    setCookie('googtrans', '/auto/' + activeLang, 365);
    setCookie('lang', activeLang, 365);

    const ZH_MAP = {
      "Welcome to JobHunt Pro": "欢迎来到 JobHunt Pro",
      "Sovereign Dashboard": "主控指挥中心",
      "Autonomous Auto-Applier": "自动投递集群",
      "ATS Resume Analyzer": "ATS 简历匹配分析器",
      "ATS Resume Sculptor": "ATS 简历雕刻分析器",
      "Live Interview Copilot": "实时面试 AI 助手",
      "AI Salary Negotiator": "智能薪资谈判助手",
      "Total Applications": "总投递职位数",
      "Success Rate": "投递成功率",
      "Response Rate": "面试回复率",
      "Active & Running": "全天候运行中",
      "Apply Now": "立即申请",
      "Upload CV & Profiles": "上传简历与个人资料",
      "Email Address": "电子邮箱地址",
      "Password": "密码",
      "Forgot Password?": "忘记密码？",
      "Remember me": "记住我",
      "Don't have an account?": "还没有账号？",
      "Already have an account?": "已有账号？",
      "Home": "首页",
      "Services": "服务",
      "Pricing": "价格",
      "Blog": "博客",
      "FAQ": "常见问题",
      "Trust": "信任",
      "Contact Us": "联系我们",
      "Contact": "联系我们",
      "Dashboard": "控制台",
      "Login": "登录",
      "Log Out": "退出登录",
      "Sign In": "登录账号",
      "Register": "注册账号",
      "Create Account": "创建新账号",
      "Start Free →": "免费开始 →",
      "Get Started Free": "免费开始体验",
      "Full Name": "姓名",
      "Phone Number": "电话号码",
      "Location": "工作地点",
      "Job Title": "职位名称",
      "Company": "公司",
      "Status": "状态",
      "Actions": "操作",
      "Date": "日期",
      "Save": "保存",
      "Cancel": "取消",
      "Submit": "提交",
      "Delete": "删除",
      "Edit": "编辑",
      "Update": "更新",
      "Close": "关闭",
      "Upload": "上传",
      "Download": "下载",
      "Search": "搜索",
      "Add": "添加",
      "Create": "创建",
      "Next": "下一步",
      "Previous": "上一步",
      "Back": "返回",
      "All Rights Reserved": "保留所有权利",
      "Privacy Policy": "隐私政策",
      "Terms of Service": "服务条款"
    };

    if (cleanCode === 'zh') {
      function translateNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
          const txt = node.nodeValue.trim();
          if (txt && ZH_MAP[txt]) {
            node.nodeValue = node.nodeValue.replace(txt, ZH_MAP[txt]);
          }
        } else if (node.nodeType === Node.ELEMENT_NODE && node.tagName !== 'SCRIPT' && node.tagName !== 'STYLE') {
          if (node.placeholder && ZH_MAP[node.placeholder.trim()]) {
            node.placeholder = ZH_MAP[node.placeholder.trim()];
          }
          if (node.title && ZH_MAP[node.title.trim()]) {
            node.title = ZH_MAP[node.title.trim()];
          }
          node.childNodes.forEach(translateNode);
        }
      }
      translateNode(document.body || document.documentElement);
    }

    try {
      if (!document.getElementById('google_translate_element')) {
        const style = document.createElement('style');
        style.innerHTML = '.goog-te-banner-frame, .goog-te-balloon-frame, #goog-gt-tt, .goog-te-spinner-pos { display: none !important; } body { top: 0px !important; }';
        document.head.appendChild(style);

        const div = document.createElement('div');
        div.id = 'google_translate_element';
        div.style.position = 'fixed';
        div.style.bottom = '-9999px';
        div.style.left = '-9999px';
        div.style.width = '1px';
        div.style.height = '1px';
        div.style.overflow = 'hidden';
        div.style.opacity = '0';
        div.style.pointerEvents = 'none';
        document.body.appendChild(div);

        window.googleTranslateElementInit = function() {
          try {
            new google.translate.TranslateElement({
              pageLanguage: 'auto',
              autoDisplay: false
            }, 'google_translate_element');
          } catch(err) {}

          let attempts = 0;
          const timer = setInterval(() => {
            attempts++;
            const select = document.querySelector('.goog-te-combo');
            if (select && select.options && select.options.length > 0) {
              let matchedOpt = Array.from(select.options).find(o => o.value.toLowerCase() === activeLang.toLowerCase() || o.value.toLowerCase() === cleanCode);
              if (matchedOpt) {
                select.value = matchedOpt.value;
                if (typeof select.onchange === 'function') select.onchange();
                select.dispatchEvent(new Event('change', { bubbles: true }));
                select.dispatchEvent(new Event('input', { bubbles: true }));
              }
            }
            if (attempts > 15) {
              clearInterval(timer);
            }
          }, 300);
        };

        const s = document.createElement('script');
        s.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
        s.async = true;
        document.head.appendChild(s);
      }
    } catch(e) {
      console.debug('GT init error:', e);
    }
  }

  // Initialize on DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      scheduleRandomToasts();
      initCommandPalette();
      initGlobalTranslationEngine();
    });
  } else {
    scheduleRandomToasts();
    initCommandPalette();
    initGlobalTranslationEngine();
  }
})();
