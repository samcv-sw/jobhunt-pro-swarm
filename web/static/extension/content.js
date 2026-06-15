// JobHunt Pro - Auto Apply Content Script
// Detects job application forms and autofills user profile data
(function () {
  'use strict';

  // === CONFIGURATION ===
  const JOB_SITES = {
    linkedin: {
      name: 'LinkedIn',
      formSelector: [
        'form.jobs-easy-apply-form',
        '[data-job-application-form]',
        'form[data-test-job-application-form]',
        '.jobs-easy-apply__content form'
      ],
      fieldMappings: {
        name: ['input[id*="first-name"]', 'input[name*="firstname"]', 'input[name*="first_name"]', '#first-name'],
        lastName: ['input[id*="last-name"]', 'input[name*="lastname"]', 'input[name*="last_name"]', '#last-name'],
        email: ['input[id*="email"]', 'input[name*="email"]', 'input[type="email"]'],
        phone: ['input[id*="phone"]', 'input[name*="phone"]', 'input[type="tel"]'],
        resume: ['input[type="file"]', 'input[id*="resume"]']
      }
    },
    indeed: {
      name: 'Indeed',
      formSelector: [
        '#ia-container',
        '.ia-IndeedApplyForm',
        '[data-testid="job-apply-form"]',
        '.jobsearch-IndeedApplyForm'
      ],
      fieldMappings: {
        name: ['input[id*="applicant.name"]', 'input[name*="fullname"]', 'input[name*="name"]', '#input-applicant\\.name'],
        email: ['input[id*="applicant.email"]', 'input[name*="email"]', 'input[type="email"]'],
        phone: ['input[id*="applicant.phone"]', 'input[name*="phone"]', 'input[type="tel"]'],
        resume: ['input[type="file"]']
      }
    },
    bayt: {
      name: 'Bayt',
      formSelector: [
        '.apply-form',
        'form[id*="apply"]',
        '.job-apply-container form'
      ],
      fieldMappings: {
        name: ['input[name*="name"]', 'input[id*="name"]'],
        email: ['input[name*="email"]', 'input[type="email"]'],
        phone: ['input[name*="phone"]', 'input[type="tel"]', 'input[name*="mobile"]'],
        resume: ['input[type="file"]']
      }
    },
    naukrigulf: {
      name: 'NaukriGulf',
      formSelector: [
        '.applyFormSec form',
        '#applyForm',
        '.jobApply form'
      ],
      fieldMappings: {
        name: ['input[name*="name"]', 'input[id*="name"]'],
        email: ['input[name*="email"]', 'input[type="email"]'],
        phone: ['input[name*="phone"]', 'input[name*="mobile"]', 'input[type="tel"]'],
        resume: ['input[type="file"]']
      }
    },
    naukri: {
      name: 'Naukri',
      formSelector: [
        '.apply-form',
        'form[id*="apply"]'
      ],
      fieldMappings: {
        name: ['input[name*="name"]', 'input[id*="name"]'],
        email: ['input[name*="email"]', 'input[type="email"]'],
        phone: ['input[name*="phone"]', 'input[name*="mobile"]', 'input[type="tel"]'],
        resume: ['input[type="file"]']
      }
    },
    glassdoor: {
      name: 'Glassdoor',
      formSelector: [
        '.css-1y9kq6x',
        '.applyFormContainer form',
        '[data-test="job-apply-form"]'
      ],
      fieldMappings: {
        name: ['input[name*="name"]', 'input[id*="name"]'],
        email: ['input[name*="email"]', 'input[type="email"]'],
        phone: ['input[name*="phone"]', 'input[type="tel"]'],
        resume: ['input[type="file"]']
      }
    },
    gulftalent: {
      name: 'GulfTalent',
      formSelector: [
        '.apply-form',
        'form.job-apply'
      ],
      fieldMappings: {
        name: ['input[name*="name"]', 'input[id*="name"]'],
        email: ['input[name*="email"]', 'input[type="email"]'],
        phone: ['input[name*="phone"]', 'input[name*="mobile"]', 'input[type="tel"]'],
        resume: ['input[type="file"]']
      }
    }
  };

  let autoApplyBtn = null;
  let settingsModal = null;
  let currentSiteConfig = null;

  // === DETECT CURRENT SITE ===
  function detectSite() {
    const host = window.location.hostname.toLowerCase();
    for (const [key, config] of Object.entries(JOB_SITES)) {
      if (host.includes(key)) return { key, ...config };
    }
    return null;
  }

  // === INJECT AUTO APPLY BUTTON ===
  function injectAutoApplyButton() {
    if (autoApplyBtn) return;

    autoApplyBtn = document.createElement('button');
    autoApplyBtn.className = 'jh-auto-apply-btn';
    autoApplyBtn.innerHTML = `
      <span class="btn-icon">⚡</span>
      <span class="btn-label">
        Auto Apply
        <span class="btn-sub">JobHunt Pro</span>
      </span>
    `;
    autoApplyBtn.title = 'Click to autofill job application form';
    autoApplyBtn.addEventListener('click', handleAutoApply);
    document.body.appendChild(autoApplyBtn);
  }

  // === MAIN AUTO APPLY HANDLER ===
  async function handleAutoApply() {
    const profile = await getProfile();
    if (!profile || !profile.name) {
      showSettingsModal();
      return;
    }

    const site = detectSite();
    if (!site) {
      showToast('No supported job form detected on this page.', 'error');
      return;
    }

    setButtonState('pending');
    try {
      const filled = await autofillForm(site, profile);
      if (filled > 0) {
        setButtonState('success');
        showToast(`✅ Filled ${filled} fields! Review and submit.`, 'success');

        // Extract job info
        const jobInfo = extractJobInfo(site);
        chrome.runtime.sendMessage({
          type: 'APPLICATION_SUBMITTED',
          data: {
            url: window.location.href,
            company: jobInfo.company,
            title: jobInfo.title,
            success: true
          }
        });
      } else {
        setButtonState('error');
        showToast('No form fields found. Try on a job application page.', 'error');
      }

      setTimeout(() => setButtonState('default'), 3000);
    } catch (err) {
      setButtonState('error');
      showToast('Autofill error: ' + err.message, 'error');
      setTimeout(() => setButtonState('default'), 3000);
    }
  }

  // === AUTOFILL THE FORM ===
  async function autofillForm(siteConfig, profile) {
    let filled = 0;

    // Find the form container
    let formContainer = null;
    for (const selector of siteConfig.formSelector) {
      try {
        formContainer = document.querySelector(selector);
        if (formContainer) break;
      } catch (e) { /* invalid selector */ }
    }

    const searchRoot = formContainer || document;

    // Map profile fields to form inputs
    const fieldMap = [
      { profileKey: 'name', selectors: siteConfig.fieldMappings.name || [], split: false },
      { profileKey: 'email', selectors: siteConfig.fieldMappings.email || [], split: false },
      { profileKey: 'phone', selectors: siteConfig.fieldMappings.phone || [], split: false },
    ];

    // Handle first/last name split
    if (siteConfig.fieldMappings.lastName) {
      const nameParts = (profile.name || '').split(' ');
      fieldMap.push({
        profileKey: 'firstName',
        value: nameParts[0] || profile.name,
        selectors: siteConfig.fieldMappings.name || [],
        split: true
      });
      fieldMap.push({
        profileKey: 'lastName',
        value: nameParts.slice(1).join(' ') || '',
        selectors: siteConfig.fieldMappings.lastName || [],
        split: true
      });
    }

    for (const field of fieldMap) {
      const value = field.value || profile[field.profileKey];
      if (!value) continue;

      for (const selector of field.selectors) {
        try {
          const inputs = searchRoot.querySelectorAll(selector);
          for (const input of inputs) {
            if (input.value && input.value.trim()) continue; // already filled
            if (input.type === 'file') continue; // skip file for now

            // Simulate real typing for framework detection
            input.focus();
            input.value = value;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new Event('blur', { bubbles: true }));

            // Visual feedback
            input.classList.add('jh-filled');
            filled++;
            break; // one match per field type is enough
          }
        } catch (e) { /* invalid selector or inaccessible */ }
        if (filled > 0 && !field.split) break;
      }
    }

    // Handle file upload for resume
    if (profile.resumeFileName && siteConfig.fieldMappings.resume) {
      for (const selector of siteConfig.fieldMappings.resume) {
        try {
          const fileInput = searchRoot.querySelector(selector);
          if (fileInput && fileInput.type === 'file') {
            // Can't programmatically set file input — show hint
            const hint = document.createElement('div');
            hint.className = 'jh-toast info';
            hint.style.cssText = 'position:relative;top:0;right:0;margin:8px 0;';
            hint.textContent = `📎 Upload your resume: "${profile.resumeFileName}"`;
            fileInput.parentElement?.appendChild(hint);
            setTimeout(() => hint.remove(), 8000);
            fileInput.classList.add('jh-filled');
            break;
          }
        } catch (e) { /* invalid selector */ }
      }
    }

    return filled;
  }

  // === EXTRACT JOB INFO ===
  function extractJobInfo(siteConfig) {
    let company = '', title = '';

    // Common selectors across sites
    const companySelectors = [
      '[data-company-name]', '.company-name', '.employer-name',
      '.job-company', '.company', '[data-test="company-name"]',
      '.jobsearch-CompanyInfoContainer', '.employer'
    ];
    const titleSelectors = [
      '[data-job-title]', '.job-title', '.job-header h1',
      'h1', '[data-test="job-title"]', '.jobsearch-JobInfoHeader-title',
      '.job-name'
    ];

    for (const sel of companySelectors) {
      const el = document.querySelector(sel);
      if (el) { company = el.textContent.trim(); break; }
    }
    for (const sel of titleSelectors) {
      const el = document.querySelector(sel);
      if (el) { title = el.textContent.trim(); break; }
    }

    return {
      company: company || siteConfig?.name || 'Unknown',
      title: title || document.title || 'Unknown'
    };
  }

  // === GET PROFILE FROM STORAGE ===
  async function getProfile() {
    return new Promise((resolve) => {
      chrome.storage.local.get('jh_profile', (data) => {
        resolve(data.jh_profile || null);
      });
    });
  }

  // === SET BUTTON STATE ===
  function setButtonState(state) {
    if (!autoApplyBtn) return;
    autoApplyBtn.className = 'jh-auto-apply-btn';
    if (state === 'pending') {
      autoApplyBtn.classList.add('pending');
      autoApplyBtn.querySelector('.btn-label').innerHTML = 'Filling...<span class="btn-sub">Working</span>';
    } else if (state === 'success') {
      autoApplyBtn.classList.add('success');
      autoApplyBtn.querySelector('.btn-label').innerHTML = '✓ Filled!<span class="btn-sub">Review & Submit</span>';
    } else if (state === 'error') {
      autoApplyBtn.classList.add('error');
      autoApplyBtn.querySelector('.btn-label').innerHTML = '× Error<span class="btn-sub">Try again</span>';
    } else {
      autoApplyBtn.querySelector('.btn-label').innerHTML = 'Auto Apply<span class="btn-sub">JobHunt Pro</span>';
    }
  }

  // === SETTINGS MODAL ===
  function showSettingsModal(focusAfterSave = false) {
    if (settingsModal) {
      settingsModal.style.display = 'flex';
      return;
    }

    getProfile().then(profile => {
      const p = profile || {};

      settingsModal = document.createElement('div');
      settingsModal.className = 'jh-modal-overlay';
      settingsModal.innerHTML = `
        <div class="jh-modal">
          <h2>⚡ JobHunt Pro Profile</h2>
          <p class="modal-sub">Fill once, apply everywhere. Your data stays in your browser.</p>

          <div class="form-group">
            <label>Full Name</label>
            <input type="text" id="jh-prof-name" value="${escapeAttr(p.name || '')}" placeholder="Sam Salameh">
          </div>

          <div class="form-group">
            <label>Email</label>
            <input type="email" id="jh-prof-email" value="${escapeAttr(p.email || '')}" placeholder="sam@example.com">
          </div>

          <div class="form-group">
            <label>Phone</label>
            <input type="tel" id="jh-prof-phone" value="${escapeAttr(p.phone || '')}" placeholder="+961 70 841 1009">
          </div>

          <div class="form-group">
            <label>LinkedIn URL</label>
            <input type="url" id="jh-prof-linkedin" value="${escapeAttr(p.linkedin || '')}" placeholder="linkedin.com/in/yourprofile">
          </div>

          <div class="form-group">
            <label>Resume File Name (for reference)</label>
            <input type="text" id="jh-prof-resume" value="${escapeAttr(p.resumeFileName || '')}" placeholder="Sam_Salameh_CV.pdf">
          </div>

          <div class="form-group">
            <label>Summary / Tagline</label>
            <textarea id="jh-prof-summary" rows="3" placeholder="Senior Network Engineer | CCNA, Fortinet NSE...">${escapeAttr(p.summary || '')}</textarea>
          </div>

          <div class="modal-actions">
            <button class="btn btn-secondary" id="jh-modal-cancel">Cancel</button>
            <button class="btn btn-primary" id="jh-modal-save">💾 Save Profile</button>
          </div>
        </div>
      `;

      document.body.appendChild(settingsModal);

      // Event listeners
      settingsModal.querySelector('#jh-modal-cancel').addEventListener('click', closeSettings);
      settingsModal.querySelector('#jh-modal-save').addEventListener('click', saveProfile);
      settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) closeSettings();
      });

      // Keyboard: Escape to close
      document.addEventListener('keydown', handleKeyDown);
    });
  }

  function handleKeyDown(e) {
    if (e.key === 'Escape' && settingsModal && settingsModal.style.display !== 'none') {
      closeSettings();
    }
  }

  function closeSettings() {
    if (settingsModal) {
      settingsModal.style.display = 'none';
    }
    document.removeEventListener('keydown', handleKeyDown);
  }

  function saveProfile() {
    const profile = {
      name: document.getElementById('jh-prof-name').value.trim(),
      email: document.getElementById('jh-prof-email').value.trim(),
      phone: document.getElementById('jh-prof-phone').value.trim(),
      linkedin: document.getElementById('jh-prof-linkedin').value.trim(),
      resumeFileName: document.getElementById('jh-prof-resume').value.trim(),
      summary: document.getElementById('jh-prof-summary').value.trim(),
      updatedAt: Date.now()
    };

    if (!profile.name) {
      showToast('Name is required!', 'error');
      return;
    }

    chrome.storage.local.set({ jh_profile: profile }, () => {
      closeSettings();
      showToast('✅ Profile saved! Click "Auto Apply" to use.', 'success');
    });
  }

  // === TOAST NOTIFICATIONS ===
  function showToast(message, type = 'info') {
    const existing = document.querySelector('.jh-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `jh-toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // === UTILITIES ===
  function escapeAttr(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // === INIT ===
  function init() {
    const site = detectSite();
    if (site) {
      currentSiteConfig = site;
      injectAutoApplyButton();
    }

    // Re-scan on DOM changes (SPAs)
    const observer = new MutationObserver(() => {
      if (!autoApplyBtn || !document.body.contains(autoApplyBtn)) {
        if (detectSite()) injectAutoApplyButton();
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  // Start after page is fully interactive
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(init, 1000);
  } else {
    window.addEventListener('load', () => setTimeout(init, 1000));
  }
})();
