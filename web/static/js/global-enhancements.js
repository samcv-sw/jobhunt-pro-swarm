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

  // Initialize on DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      scheduleRandomToasts();
      initCommandPalette();
    });
  } else {
    scheduleRandomToasts();
    initCommandPalette();
  }
})();
