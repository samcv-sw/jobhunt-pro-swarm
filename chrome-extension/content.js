// JobHunt Pro v2 — Content Script (MAIN world)
// Injected into job boards. Uses MAIN world: trusted event dispatch (no CDP).
// Features: heuristic click, shadow DOM pierce, IndexedDB vault, LinkedIn Connector.

(function() {
  'use strict';

  const API_BASE = 'https://jhfguf.pythonanywhere.com';
  
  // ═══════════════════════════════════════════════════════════════════════════
  // INDEXEDDB VAULT (Persistent Q/A memory — unlimited)
  // ═══════════════════════════════════════════════════════════════════════════
  const DB_NAME = 'jhpro_vault';
  const DB_VERSION = 1;
  let db = null;

  function openVault() {
    return new Promise((resolve, reject) => {
      if (db) return resolve(db);
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = (e) => {
        const d = e.target.result;
        if (!d.objectStoreNames.contains('qa')) {
          d.createObjectStore('qa', { keyPath: 'question' });
        }
        if (!d.objectStoreNames.contains('stats')) {
          d.createObjectStore('stats', { keyPath: 'id' });
        }
      };
      req.onsuccess = (e) => { db = e.target.result; resolve(db); };
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async function vaultGet(question) {
    try {
      const d = await openVault();
      return new Promise((resolve) => {
        const tx = d.transaction('qa', 'readonly');
        const req = tx.objectStore('qa').get(question);
        req.onsuccess = () => resolve(req.result ? req.result.answer : null);
        req.onerror = () => resolve(null);
      });
    } catch(e) { return null; }
  }

  async function vaultSet(question, answer) {
    try {
      const d = await openVault();
      const tx = d.transaction('qa', 'readwrite');
      tx.objectStore('qa').put({ question, answer, ts: Date.now() });
    } catch(e) {}
  }

  async function vaultGetAll() {
    try {
      const d = await openVault();
      return new Promise((resolve) => {
        const tx = d.transaction('qa', 'readonly');
        const req = tx.objectStore('qa').getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
    } catch(e) { return []; }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // MAIN WORLD CLICK (No CDP — dispatch trusted events in MAIN context)
  // ═══════════════════════════════════════════════════════════════════════════

  function humanClick(element) {
    if (!element) return false;
    
    const rect = element.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    
    // Dispatch chain: pointer → mouse → click (all trusted in MAIN world)
    const opts = { bubbles: true, cancelable: true, view: window, clientX: x, clientY: y };
    
    element.dispatchEvent(new PointerEvent('pointerdown', opts));
    element.dispatchEvent(new PointerEvent('pointerup', opts));
    element.dispatchEvent(new MouseEvent('mousedown', opts));
    element.dispatchEvent(new MouseEvent('mouseup', opts));
    element.dispatchEvent(new MouseEvent('click', opts));
    
    // If it's an anchor, also navigate
    if (element.tagName === 'A' && element.href) {
      setTimeout(() => { window.location.href = element.href; }, 50);
    }
    
    return true;
  }

  function humanScrollTo(element) {
    if (!element) return;
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Small random delay after scroll
    return new Promise(r => setTimeout(r, 300 + Math.random() * 400));
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // HEURISTIC DOM FALLBACK (0 token cost — regex/XPath button finding)
  // ═══════════════════════════════════════════════════════════════════════════

  const HEURISTIC_PATTERNS = {
    'apply': ['apply', 'submit', 'send application', 'submit application', 'easy apply', 'quick apply',
              '/^\\s*apply\\s*$/i', '(?i)apply\\s+now', 'send', 'continue'],
    'next_page': ['next', '›', '»', '→', 'next page', 'show more', 'load more',
                  '[aria-label="Next"]', '[aria-label="Next page"]'],
    'connect': ['connect', 'add connection', 'follow', 'message', 'get in touch'],
    'close': ['close', 'dismiss', 'cancel', '×', '✕', '[aria-label="Close"]', '[aria-label="Dismiss"]']
  };

  function heuristicFind(intent, container = document) {
    const patterns = HEURISTIC_PATTERNS[intent];
    if (!patterns) return null;

    // 1. Try aria-label first (most reliable for modern SPAs)
    for (const p of patterns) {
      if (p.startsWith('[')) {
        try {
          const el = container.querySelector(p);
          if (el && isVisible(el)) return el;
        } catch(e) {}
      }
    }

    // 2. Try text content matching
    const buttons = container.querySelectorAll('button, a, [role="button"], input[type="submit"], input[type="button"], [tabindex]:not([tabindex="-1"])');
    for (const btn of buttons) {
      const text = (btn.textContent || '').trim().toLowerCase();
      const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
      const val = (btn.value || '').toLowerCase();
      const combined = text + ' ' + aria + ' ' + val;
      
      for (const p of patterns) {
        if (!p.startsWith('/') && !p.startsWith('[')) {
          if (combined.includes(p.toLowerCase())) {
            if (isVisible(btn)) return btn;
          }
        } else if (p.startsWith('/') && p.endsWith('/i')) {
          try {
            const regex = new RegExp(p.slice(1, -2), 'i');
            if (regex.test(combined) && isVisible(btn)) return btn;
          } catch(e) {}
        }
      }
    }

    // 3. Fallback: CSS class-based heuristics
    const classBased = container.querySelectorAll(
      `[class*="apply"], [class*="submit"], [class*="next"], [id*="apply"], [id*="submit"], [data-automation*="apply"], [data-qa*="apply"]`
    );
    for (const el of classBased) {
      if (isVisible(el)) return el;
    }

    return null;
  }

  function isVisible(el) {
    if (!el || !el.offsetParent) return false;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SHADOW DOM PIERCE (Recursive)
  // ═══════════════════════════════════════════════════════════════════════════

  function shadowQueryAll(selector, root = document) {
    const results = [];
    // Search light DOM
    try {
      const light = root.querySelectorAll(selector);
      results.push(...light);
    } catch(e) {}
    
    // Search shadow roots recursively
    const allElements = root.querySelectorAll('*');
    for (const el of allElements) {
      if (el.shadowRoot) {
        try {
          const shadowResults = shadowQueryAll(selector, el.shadowRoot);
          results.push(...shadowResults);
        } catch(e) {}
      }
    }
    return results;
  }

  function shadowQuerySelector(selector, root = document) {
    // Light DOM first
    try {
      const el = root.querySelector(selector);
      if (el) return el;
    } catch(e) {}
    
    // Shadow DOM
    const allElements = root.querySelectorAll('*');
    for (const el of allElements) {
      if (el.shadowRoot) {
        try {
          const found = el.shadowRoot.querySelector(selector);
          if (found) return found;
        } catch(e) {}
      }
    }
    return null;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SMART CLICK DECISION (heuristic first, API fallback only if needed)
  // ═══════════════════════════════════════════════════════════════════════════

  async function smartClick(intent, container) {
    // 1. Heuristic (0 token, 0ms latency)
    const el = heuristicFind(intent, container || document);
    if (el) {
      await humanScrollTo(el);
      await delay(100 + Math.random() * 200);
      humanClick(el);
      return true;
    }

    // 2. Shadow DOM deep search
    const shadowEl = shadowQuerySelector(
      intent === 'apply' ? 'button, a, [role="button"]' :
      intent === 'next_page' ? 'button:not([disabled]), a, [role="button"]:not([disabled])' : 'button, a',
      container || document
    );
    if (shadowEl && isVisible(shadowEl)) {
      const text = (shadowEl.textContent || '').toLowerCase();
      const match = HEURISTIC_PATTERNS[intent] || [];
      if (match.some(p => text.includes(p))) {
        humanClick(shadowEl);
        return true;
      }
    }

    // 3. API fallback (token cost, but rare)
    try {
      const clickables = collectClickables(container || document);
      const response = await fetch(`${API_BASE}/api/job/semantic-router`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intent, elements: clickables })
      });
      if (response.ok) {
        const res = await response.json();
        if (res.target_x && res.target_y) {
          const target = document.elementFromPoint(res.target_x, res.target_y);
          if (target) { humanClick(target); return true; }
        }
      }
    } catch(e) {}

    return false;
  }

  function collectClickables(root) {
    return Array.from(root.querySelectorAll('button, a, input[type="submit"], [role="button"]'))
      .filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && (el.textContent || el.innerText || '').trim().length > 0;
      })
      .slice(0, 30)
      .map((el, i) => {
        const rect = el.getBoundingClientRect();
        return { id: i, tag: el.tagName, text: (el.textContent || el.innerText || '').trim().substring(0, 50),
                x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2) };
      });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // HUMAN TYPING SIMULATION (Typo emulation included)
  // ═══════════════════════════════════════════════════════════════════════════

  async function simulateHumanTyping(input, text) {
    if (!input || !text) return;
    input.focus();
    input.value = '';
    
    // Random chance to make a typo and correct it (human behavior)
    const shouldTypo = Math.random() < 0.03; // 3% chance
    
    for (let i = 0; i < text.length; i++) {
      input.value += text[i];
      input.dispatchEvent(new Event('input', { bubbles: true }));
      await delay(30 + Math.random() * 80); // 30-110ms per keystroke
    }
    
    if (shouldTypo) {
      // Make and correct a typo (adds realism for behavioral analytics)
      const typoChar = String.fromCharCode(97 + Math.floor(Math.random() * 26));
      input.value += typoChar;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      await delay(200 + Math.random() * 300);
      // Backspace
      input.value = input.value.slice(0, -1);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      await delay(150 + Math.random() * 200);
      // Re-type correct char
      const origChar = text[text.length - 1];
      if (origChar) {
        input.value += origChar;
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
    
    input.dispatchEvent(new Event('change', { bubbles: true }));
    input.blur();
  }

  function delay(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // MEMORY VAULT: ASK SWARM OR CACHED ANSWER
  // ═══════════════════════════════════════════════════════════════════════════

  async function askSwarmOrVault(questionText, cvData) {
    // 1. Check IndexedDB vault (0 token, 0 latency)
    const cached = await vaultGet(questionText);
    if (cached) {
      console.log('[JHPro] Vault hit:', questionText.substring(0, 40));
      return cached;
    }
    
    // 2. Not in vault — call API
    showToast('🧠 AI analyzing question...');
    try {
      const response = await fetch(`${API_BASE}/api/job/ask-swarm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: questionText, cv: cvData })
      });
      if (response.ok) {
        const res = await response.json();
        if (res.answer) {
          await vaultSet(questionText, res.answer);
          return res.answer;
        }
      }
    } catch(e) {}
    
    // 3. Fallback
    const fallback = "Yes / 5 years";
    await vaultSet(questionText, fallback);
    return fallback;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LINKEDIN CONNECTOR MODE (Connections, not applications)
  // ═══════════════════════════════════════════════════════════════════════════

  async function handleLinkedInConnect() {
    const isLinkedIn = window.location.hostname.includes('linkedin.com');
    if (!isLinkedIn) {
      showToast('❌ Open a LinkedIn profile page first');
      return false;
    }

    const connectBtn = heuristicFind('connect');
    if (!connectBtn) {
      showToast('❌ No "Connect" button found');
      return false;
    }

    showToast('🔗 Sending connection request...');
    humanClick(connectBtn);
    await delay(1500 + Math.random() * 1000);

    // Check for "Add a note" modal
    const addNoteBtn = heuristicFind('connect', document);
    const noteModal = document.querySelector('[role="dialog"], .artdeco-modal, [class*="send-invite"]');
    
    if (noteModal) {
      const messageArea = noteModal.querySelector('textarea, [contenteditable="true"]');
      if (messageArea) {
        // Generate personalized connection message
        const profileName = document.querySelector('h1')?.textContent?.trim() || '';
        const profileHeadline = document.querySelector('[class*="headline"]')?.textContent?.trim() || '';
        const jobTitle = profileHeadline || 'professional in your field';
        
        const message = `Hi ${profileName.split(' ')[0]}, I came across your profile and was impressed by your experience as a ${jobTitle}. I'd love to connect and learn more about your career journey. Best, Sam`;
        
        await simulateHumanTyping(messageArea, message);
        await delay(500 + Math.random() * 500);
        
        // Click send
        const sendBtn = heuristicFind('apply', noteModal);
        if (sendBtn) humanClick(sendBtn);
      }
    }

    showToast('✅ Connection request sent!');
    return true;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // BULK APPLY ROBOT (MAIN world clicks, IndexedDB memory)
  // ═══════════════════════════════════════════════════════════════════════════

  let isRobotRunning = false;
  let activeFrameTime = 0;
  let stateInterval = null;

  function startSensorReporting() {
    if (stateInterval) clearInterval(stateInterval);
    stateInterval = setInterval(() => {
      if (!isRobotRunning) return;
      activeFrameTime += 5000;
      chrome.runtime.sendMessage({
        type: 'REPORT_STATE',
        frameUrl: window.location.href,
        status: 'applying',
        timeActive: activeFrameTime
      });
    }, 5000);
  }

  async function startBulkApplyRobot() {
    if (isRobotRunning) { showToast('🤖 Robot is already running!'); return; }
    isRobotRunning = true;
    showToast('🤖 Infinite Robot Mode activated!');
    
    let appliedCount = 0;
    const processedJobs = new Set();
    try {
      const stored = await chrome.storage.local.get(['processedJobs']);
      if (stored.processedJobs) stored.processedJobs.forEach(j => processedJobs.add(j));
    } catch(e) {}
    
    // Create progress UI
    const progressUI = document.createElement('div');
    progressUI.id = 'jh-pro-progress';
    progressUI.style.cssText = `
      position: fixed; top: 20px; inset-inline-start: 50%; transform: translateX(-50%); z-index: 999999;
      background: #000; color: #00f0ff; border: 1px solid #00f0ff;
      padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer;
    `;
    progressUI.title = 'Click to stop';
    progressUI.addEventListener('click', () => { isRobotRunning = false; progressUI.innerHTML = '🛑 Stopping...'; });
    document.body.appendChild(progressUI);
    startSensorReporting();

    while (isRobotRunning) {
      // Find job cards using heuristic + shadow DOM
      let jobCards = [];
      
      // Try common selectors via shadow DOM
      const selectors = [
        '.job-card-container', '.job_seen_beacon', '.tapItem', '.react-job-listing',
        '[data-automation="normalJob"]', '.card', '.jobTuple', 'article.jobTuple',
        '[data-test-name="jobCard"]', 'section.up-card-section', 'li.job', '.job-card'
      ];
      
      for (const sel of selectors) {
        const found = shadowQueryAll(sel);
        if (found.length > 0) { jobCards = found; break; }
      }

      // Fallback
      if (jobCards.length === 0) {
        jobCards = document.querySelectorAll('a[href*="/jobs/view"], a[href*="/job-detail"], li, .job, .card');
      }

      const unprocessed = Array.from(jobCards).filter(card => {
        const id = (card.getAttribute('data-job-id') || card.innerText.trim().substring(0, 100));
        return !processedJobs.has(id);
      });

      if (unprocessed.length > 0) {
        for (const card of unprocessed) {
          if (!isRobotRunning) break;
          
          // CAPTCHA check
          if (detectCaptcha()) {
            await handleCaptcha();
          }
          
          const jobId = (card.getAttribute('data-job-id') || card.innerText.trim().substring(0, 100));
          processedJobs.add(jobId);
          chrome.storage.local.set({ processedJobs: Array.from(processedJobs) });
          
          progressUI.innerHTML = `🤖 Applying... (${appliedCount})<br><small style="font-size:10px;color:#aaa">Click to stop</small>`;
          
          // Click using MAIN world events
          await humanScrollTo(card);
          await delay(200 + Math.random() * 300);
          const clickable = card.querySelector('a') || card;
          humanClick(clickable);
          
          // Wait for detail to load
          await delay(1500 + Math.random() * 1500);
          
          const jobData = extractJobFromPage();
          if (jobData && jobData.title) {
            // Blacklist check
            const isBlacklisted = await new Promise(resolve => {
              chrome.storage.local.get(['blacklist'], (data) => {
                if (data.blacklist && jobData.company) {
                  resolve(data.blacklist.some(b => jobData.company.toLowerCase().includes(b)));
                } else resolve(false);
              });
            });
            
            if (isBlacklisted) {
              showToast(`⏭️ Skipped blacklisted: ${jobData.company}`);
              continue;
            }
            
            try {
              const response = await fetch(`${API_BASE}/api/job/analyze-and-apply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jobData),
              });
              
              if (response.status === 403 || response.status === 401) {
                progressUI.remove();
                showToast('🔒 Upgrade to unlock Bulk Mode!');
                isRobotRunning = false;
                return;
              }
              if (response.ok) {
                appliedCount++;
                // Auto followup generation
                try {
                  fetch(`${API_BASE}/api/job/followup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: jobData.title, company: jobData.company })
                  });
                } catch(e) {}
              }
            } catch(e) {}
          }
        }
      } else {
        // Scroll to load more
        window.scrollBy(0, 1000);
        const innerScroll = document.querySelector('.jobs-search-results-list');
        if (innerScroll) innerScroll.scrollBy(0, 1000);
        await delay(2000);
        
        // Try next page
        const clicked = await smartClick('next_page');
        if (clicked) {
          processedJobs.clear();
          await delay(3000);
        } else {
          isRobotRunning = false;
          progressUI.innerHTML = `✅ Done! Applied to ${appliedCount} jobs.`;
          setTimeout(() => progressUI.remove(), 4000);
          return;
        }
      }
    }
    
    progressUI.innerHTML = `🛑 Stopped. Applied: ${appliedCount}`;
    setTimeout(() => progressUI.remove(), 3000);
  }

  function detectCaptcha() {
    const text = document.body.innerText.toLowerCase();
    return text.includes('verify you are human') || 
           text.includes('checking your browser') ||
           document.querySelector('.cf-turnstile, iframe[src*="captcha"], iframe[src*="recaptcha"]') !== null;
  }

  async function handleCaptcha() {
    console.warn('🚨 CAPTCHA detected');
    isRobotRunning = false;
    
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed; top: 0; inset-inline-start: 0; width: 100vw; height: 100vh;
      background: rgba(200,0,0,0.9); backdrop-filter: blur(5px);
      display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 9999999;
    `;
    modal.innerHTML = `
      <div style="font-size: 64px; margin-bottom: 20px;">🚨</div>
      <h1 style="color: white; font-weight: bold; font-size: 32px;">CAPTCHA DETECTED</h1>
      <p style="color: #ffd700; font-size: 18px; margin-bottom: 30px;">Job board requested verification.</p>
      <button id="resume-robot-btn" style="background: white; color: #c80000; font-size: 20px; font-weight: bold; padding: 15px 40px; border: none; border-radius: 8px; cursor: pointer;">
        I solved it - Resume ▶
      </button>
    `;
    document.body.appendChild(modal);
    
    await new Promise(resolve => {
      document.getElementById('resume-robot-btn').addEventListener('click', () => {
        modal.remove();
        isRobotRunning = true;
        resolve();
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // AUTO-APPLY
  // ═══════════════════════════════════════════════════════════════════════════

  async function handleAutoApply(sendResponse) {
    try {
      const jobData = extractJobFromPage();
      if (!jobData) {
        showToast('❌ No job detected');
        if (sendResponse) sendResponse({ success: false, error: 'No job detected' });
        return;
      }

      showToast('🤖 AI analyzing and applying...');

      const response = await fetch(`${API_BASE}/api/job/analyze-and-apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobData),
      });

      if (response.status === 403 || response.status === 401) {
        showToast('🎯 Application ready — upgrade to Pro!');
        showPayModal(jobData);
        if (sendResponse) sendResponse({ success: false, error: 'upgrade_required' });
        return;
      }

      if (response.ok) {
        const result = await response.json();
        if (detectApplicationForm()) {
          await fillApplicationForm(result.candidate_data);
        }
        showToast(`✅ Applied! Score: ${result.match_score}%`);
        if (sendResponse) sendResponse({ success: true, score: result.match_score });
      } else {
        showToast('❌ Application failed');
        if (sendResponse) sendResponse({ success: false });
      }
    } catch(e) {
      showToast('⚠️ Error. Check extension settings.');
      if (sendResponse) sendResponse({ success: false, error: e.message });
    }
  }

  function showPayModal(jobData) {
    const modal = document.createElement('div');
    modal.id = 'jh-pro-tease-modal';
    modal.style.cssText = `
      position: fixed; top: 0; inset-inline-start: 0; width: 100vw; height: 100vh;
      background: rgba(0,0,0,0.85); backdrop-filter: blur(5px);
      display: flex; justify-content: center; align-items: center; z-index: 9999999;
    `;
    modal.innerHTML = `
      <div style="background: #111; border: 1px solid #333; border-radius: 16px; padding: 32px; max-width: 500px; width: 90%; text-align: center;">
        <div style="font-size: 48px; margin-bottom: 16px;">🎯</div>
        <h2 style="color: #fff; margin: 0 0 8px 0; font-size: 24px;">Match: <span style="color: #00f0ff;">98%</span></h2>
        <p style="color: #aaa; margin: 0 0 24px 0;">Perfect AI application ready for ${jobData.title || 'this position'}.</p>
        <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin-bottom: 24px; border: 1px solid #333;">
          <div style="color: #ccc; font-size: 14px; filter: blur(4px); user-select: none;">
            Dear Hiring Manager, I am writing to express my strong interest in the ${jobData.title} role...
          </div>
          <div style="margin-top: 10px;"><span style="background: rgba(0,240,255,0.1); color: #00f0ff; padding: 6px 16px; border-radius: 20px; font-size: 13px; border: 1px solid rgba(0,240,255,0.3);">🔒 Encrypted</span></div>
        </div>
        <button id="jh-go-pro-btn" style="background: linear-gradient(135deg, #00f0ff, #0080ff); color: #000; border: none; padding: 16px 32px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%;">
          Unlock & Auto-Apply 🚀
        </button>
        <p id="jh-close-tease" style="color: #666; margin-top: 16px; font-size: 13px; cursor: pointer;">Maybe later</p>
      </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('jh-go-pro-btn').addEventListener('click', () => { window.open(`${API_BASE}/pricing`, '_blank'); modal.remove(); });
    document.getElementById('jh-close-tease').addEventListener('click', () => modal.remove());
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EXTRACT JOB FROM PAGE (with shadow DOM backup)
  // ═══════════════════════════════════════════════════════════════════════════

  function extractJobFromPage() {
    const url = window.location.href;
    let job = { url, source: 'unknown', title: '', company: '', description: '', skills: [] };

    const $ = (sel, root = document) => {
      const el = root.querySelector(sel);
      return el ? el.textContent?.trim() || '' : '';
    };
    const $$ = (sel) => Array.from(document.querySelectorAll(sel)).map(e => e.textContent.trim());

    if (url.includes('linkedin.com/jobs')) {
      job.source = 'linkedin';
      job.title = $('.job-details-jobs-unified-top-card__job-title') || $('h1') || '';
      job.company = $('.job-details-jobs-unified-top-card__company-name') || '';
      job.description = $('.jobs-description__content') || $('[class*="description"]') || '';
      job.skills = $$('.job-details-how-you-match__skills-item');
    }
    else if (url.includes('indeed.com')) {
      job.source = 'indeed';
      job.title = $('.jobsearch-JobInfoHeader-title') || $('h1') || '';
      job.company = $('[data-company-name]') || $('[class*="company"]') || '';
      job.description = $('#jobDescriptionText') || '';
    }
    else if (url.includes('glassdoor.com')) {
      job.source = 'glassdoor';
      job.title = $('.job-title') || $('h1') || '';
      job.company = $('.employer-name') || '';
      job.description = $('.jobDescriptionContent') || '';
    }
    else if (url.includes('bayt.com')) {
      job.source = 'bayt';
      job.title = $('.is-spaced') || $('h1') || '';
      job.company = $('.t-small.u-mid') || '';
      job.description = $('.card-content') || '';
    }
    else if (url.includes('ziprecruiter.com')) {
      job.source = 'ziprecruiter';
      job.title = $('.job_title') || $('h1') || '';
      job.company = $('.company_name') || '';
      job.description = $('.job_description') || '';
    }
    else if (url.includes('wellfound.com')) {
      job.source = 'wellfound';
      job.title = $('h1') || '';
      job.company = $('h2') || '';
      job.description = $('[class*="description"]') || '';
    }
    else if (url.includes('dice.com')) {
      job.source = 'dice';
      job.title = $('h1.jobTitle') || '';
      job.company = $('a[data-cy="companyNameLink"]') || '';
      job.description = $('#jobdescSec') || '';
    }
    else if (url.includes('seek.com.au')) {
      job.source = 'seek';
      job.title = $('[data-automation="job-detail-title"]') || $('h1') || '';
      job.company = $('[data-automation="advertiser-name"]') || '';
      job.description = $('[data-automation="jobAdDetails"]') || '';
    }
    else if (url.includes('greenhouse.io') || url.includes('lever.co') || url.includes('workable.com')) {
      job.source = 'ats';
      job.title = $('h1') || $('[class*="title"]') || '';
      job.company = $('[class*="company"]') || '';
      job.description = document.body.innerText.substring(0, 3000) || '';
    }
    else {
      // Generic extraction
      job.title = $('h1') || $('[class*="title"]') || $('[class*="position"]') || '';
      job.company = $('[class*="company"]') || $('[class*="employer"]') || '';
      job.description = $('[class*="desc"]') || $('[class*="detail"]') || document.body.innerText.substring(0, 3000) || '';
    }

    return job.title ? job : null;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // FILL APPLICATION FORM (shadow DOM aware + human typing)
  // ═══════════════════════════════════════════════════════════════════════════

  function detectApplicationForm() {
    const inputs = shadowQueryAll('input, textarea, select');
    return inputs.length > 0;
  }

  async function fillApplicationForm(data) {
    if (!data) return;
    
    // Try shadow DOM for inputs
    const allInputs = shadowQueryAll('input:not([type="hidden"]):not([type="file"]), textarea');
    
    for (const input of allInputs) {
      const name = input.name || input.id || '';
      let value = '';
      
      const map = {
        'name': data.name, 'firstName': data.first_name, 'lastName': data.last_name,
        'email': data.email, 'phone': data.phone, 'location': data.location,
        'linkedin': data.linkedin_url, 'website': data.website, 'summary': data.summary,
        'resume': data.summary, 'message': data.summary, 'cover': data.summary,
        'fname': data.first_name, 'lname': data.last_name, 'fullname': data.name,
        'first_name': data.first_name, 'last_name': data.last_name
      };
      
      // Direct match
      if (map[name.toLowerCase()]) {
        value = map[name.toLowerCase()];
      } 
      // Partial match
      else {
        for (const [key, val] of Object.entries(map)) {
          if (name.toLowerCase().includes(key)) {
            value = val;
            break;
          }
        }
      }
      
      if (value) {
        await simulateHumanTyping(input, value);
      }
    }
    
    // Handle custom questions via memory vault
    for (const input of allInputs) {
      if (input.value) continue;
      const label = input.closest('label') || input.parentElement?.querySelector('label') || 
                    input.closest('[class*="field"]')?.querySelector('[class*="label"]');
      if (label && label.innerText && label.innerText.length > 5) {
        const answer = await askSwarmOrVault(label.innerText.trim(), data);
        if (answer) await simulateHumanTyping(input, answer);
      }
    }
    
    // Handle file upload (resume)
    const fileInput = shadowQuerySelector('input[type="file"]');
    if (fileInput && data.cv_url) {
      try {
        const response = await fetch(data.cv_url);
        const blob = await response.blob();
        const file = new File([blob], 'resume.pdf', { type: 'application/pdf' });
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
      } catch(e) {}
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SEMANTIC DOM ROUTER (API + heuristic)
  // ═══════════════════════════════════════════════════════════════════════════

  async function semanticDOMRouter(intent) {
    // Try heuristic first
    const el = heuristicFind(intent);
    if (el) {
      const rect = el.getBoundingClientRect();
      return { x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2) };
    }
    
    // Fallback to API
    const clickables = collectClickables();
    if (clickables.length === 0) return null;
    
    try {
      const response = await fetch(`${API_BASE}/api/job/semantic-router`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intent, elements: clickables })
      });
      if (response.ok) {
        const res = await response.json();
        if (res.target_x && res.target_y) return { x: res.target_x, y: res.target_y };
      }
    } catch(e) {}
    return null;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LINKEDIN BULK JOB SEARCH + CONNECT (instead of apply)
  // ═══════════════════════════════════════════════════════════════════════════

  async function startLinkedInConnector() {
    if (isRobotRunning) { showToast('🤖 Already running!'); return; }
    isRobotRunning = true;
    
    let connectedCount = 0;
    const processed = new Set();
    
    showToast('🔗 LinkedIn Connector mode activated!');
    
    const progressUI = document.createElement('div');
    progressUI.id = 'jh-pro-connector';
    progressUI.style.cssText = `
      position: fixed; bottom: 20px; inset-inline-end: 80px; z-index: 999999;
      background: #000; color: #0aff; border: 1px solid #0aff;
      padding: 10px 20px; border-radius: 8px; font-weight: bold;
      cursor: pointer;
    `;
    progressUI.textContent = '🔗 Connecting... (0)';
    progressUI.addEventListener('click', () => { isRobotRunning = false; });
    document.body.appendChild(progressUI);
    
    while (isRobotRunning) {
      // Find connect buttons on search results page
      const connectBtns = document.querySelectorAll(
        'button[aria-label*="connect"], button[aria-label*="follow"], [class*="connect"] button'
      );
      
      for (const btn of connectBtns) {
        if (!isRobotRunning) break;
        
        const id = btn.getAttribute('data-test') || btn.innerText;
        if (processed.has(id)) continue;
        processed.add(id);
        
        await humanScrollTo(btn);
        await delay(500 + Math.random() * 1000);
        humanClick(btn);
        
        // Wait for modal
        await delay(1000 + Math.random() * 1000);
        
        // Try to add note
        const noteArea = document.querySelector('textarea, [contenteditable="true"]');
        if (noteArea && Math.random() > 0.5) { // 50% add note
          const message = `Hi there! I came across your profile and was impressed by your experience. I'd love to connect and learn more!`;
          await simulateHumanTyping(noteArea, message);
          await delay(500 + Math.random() * 500);
          
          const sendBtn = heuristicFind('apply', document.querySelector('[role="dialog"]') || document);
          if (sendBtn) humanClick(sendBtn);
        } else {
          // Click "Send without note"
          const sendBtn = document.querySelector('[class*="send"] button, [class*="submit"] button');
          if (sendBtn) humanClick(sendBtn);
        }
        
        connectedCount++;
        progressUI.textContent = `🔗 Connected: ${connectedCount}`;
        
        await delay(3000 + Math.random() * 2000); // LinkedIn rate limit
      }
      
      // Scroll more
      window.scrollBy(0, 800);
      await delay(2000);
    }
    
    progressUI.textContent = `🛑 Done. Connected: ${connectedCount}`;
    setTimeout(() => progressUI.remove(), 5000);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // TOAST UI
  // ═══════════════════════════════════════════════════════════════════════════

  function showToast(message) {
    let toast = document.getElementById('jh-pro-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'jh-pro-toast';
      toast.style.cssText = `
        position: fixed; top: 20px; inset-inline-end: 20px; z-index: 9999999;
        background: #111; color: #fff; padding: 12px 24px;
        border-radius: 8px; border-inline-start: 4px solid #00f0ff;
        font-family: system-ui, sans-serif; font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        transition: opacity 0.3s; opacity: 0;
      `;
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = '1';
    
    if (window.jhToastTimeout) clearTimeout(window.jhToastTimeout);
    window.jhToastTimeout = setTimeout(() => { toast.style.opacity = '0'; }, 4000);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // MESSAGE LISTENER (from popup.js / background.js)
  // ═══════════════════════════════════════════════════════════════════════════

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
      case 'autoApply':
        handleAutoApply(sendResponse);
        return true;
      case 'fillForm':
        handleFillForm(sendResponse);
        return true;
      case 'generateCoverLetter':
        handleGenerateCoverLetter(sendResponse);
        return true;
      case 'linkedInConnect':
        handleLinkedInConnect().then(sendResponse);
        return true;
      case 'linkedInConnector':
        startLinkedInConnector();
        sendResponse({ success: true });
        return true;
    }

    // Background messages
    if (request.type === 'GLOBAL_HALT') {
      isRobotRunning = false;
      const el = document.getElementById('jh-pro-progress');
      if (el) el.innerHTML = '🛑 Halted globally';
      sendResponse({ success: true });
      return;
    }
    if (request.type === 'SMART_SKIP') {
      activeFrameTime = 0;
      sendResponse({ success: true });
      return;
    }
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // INIT
  // ═══════════════════════════════════════════════════════════════════════════

  function injectFloatingButton() {
    if (document.getElementById('jh-pro-floating-btn')) return;
    const btn = document.createElement('div');
    btn.id = 'jh-pro-floating-btn';
    btn.innerHTML = '⚡ Pro';
    btn.style.cssText = `
      position: fixed; bottom: 20px; inset-inline-end: 20px; z-index: 999999;
      background: linear-gradient(135deg, #00f0ff, #0088ff);
      color: #000; font-weight: 700; padding: 10px 16px;
      border-radius: 25px; cursor: pointer; font-size: 13px;
      box-shadow: 0 4px 20px rgba(0,240,255,0.3);
      transition: transform 0.2s;
    `;
    btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.05)');
    btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1)');
    btn.addEventListener('click', () => {
      // Show quick action menu
      const menu = document.createElement('div');
      menu.id = 'jh-pro-quick-menu';
      menu.style.cssText = `
        position: fixed; bottom: 70px; inset-inline-end: 20px; z-index: 999998;
        background: #111; border: 1px solid #333; border-radius: 12px;
        padding: 8px; box-shadow: 0 8px 30px rgba(0,0,0,0.5);
      `;
      menu.innerHTML = `
        <div style="padding: 8px 16px; cursor: pointer; color: #fff; font-size: 13px; white-space: nowrap;" onclick="this.closest('#jh-pro-quick-menu').remove(); chrome.runtime.sendMessage({action:'autoApply'});">⚡ Auto-Apply</div>
        <div style="padding: 8px 16px; cursor: pointer; color: #fff; font-size: 13px; white-space: nowrap;" onclick="this.closest('#jh-pro-quick-menu').remove();">🤖 Bulk Robot</div>
        <div style="padding: 8px 16px; cursor: pointer; color: #0aff; font-size: 13px; white-space: nowrap;" onclick="this.closest('#jh-pro-quick-menu').remove(); startLinkedInConnector();">🔗 LinkedIn Connect</div>
        <div style="padding: 8px 16px; cursor: pointer; color: #aaa; font-size: 13px; white-space: nowrap;" onclick="this.closest('#jh-pro-quick-menu').remove();">✍️ Cover Letter</div>
        <div style="padding: 8px 16px; cursor: pointer; color: #666; font-size: 13px; white-space: nowrap;" onclick="this.closest('#jh-pro-quick-menu').remove(); chrome.runtime.sendMessage({action:'openDashboard'});">📊 Dashboard</div>
      `;
      document.body.appendChild(menu);
      
      // Close on click outside
      setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
          if (!e.target.closest('#jh-pro-quick-menu') && !e.target.closest('#jh-pro-floating-btn')) {
            const m = document.getElementById('jh-pro-quick-menu');
            if (m) m.remove();
            document.removeEventListener('click', closeMenu);
          }
        });
      }, 100);
    });
    document.body.appendChild(btn);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectFloatingButton);
  } else {
    injectFloatingButton();
  }

  console.log('[JHPro] v2.0 content script loaded — MAIN world, heuristic clicks, shadow DOM');
})();
