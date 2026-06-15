// JobHunt Pro - Content Script
// Injected into LinkedIn, Indeed, Glassdoor, Bayt, ZipRecruiter, etc.
(function() {
  'use strict';

  const API_BASE = 'https://jhfguf.pythonanywhere.com';
  let userData = null;

  // ── Init ──
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
      case 'autoApply': handleAutoApply(sendResponse); return true;
      case 'fillForm': handleFillForm(sendResponse); return true;
      case 'generateCoverLetter': handleGenerateCoverLetter(sendResponse); return true;
    }
  });

  // ── Inject floating button ──
  function injectFloatingButton() {
    if (document.getElementById('jh-pro-floating-btn')) return;
    
    const btn = document.createElement('div');
    btn.id = 'jh-pro-floating-btn';
    btn.innerHTML = '⚡ Auto-Apply';
    btn.style.cssText = `
      position: fixed; bottom: 20px; right: 20px; z-index: 999999;
      background: linear-gradient(135deg, #00f0ff, #0088ff);
      color: #000; font-weight: 700; padding: 12px 20px;
      border-radius: 25px; cursor: pointer; font-size: 14px;
      box-shadow: 0 4px 20px rgba(0,240,255,0.3);
      transition: transform 0.2s;
    `;
    btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.05)');
    btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1)');
    btn.addEventListener('click', handleAutoApply);
    document.body.appendChild(btn);
  }

  // ── Auto-Apply ──
  async function handleAutoApply(sendResponse) {
    try {
      // Extract job details from page
      const jobData = extractJobFromPage();
      if (!jobData) {
        showToast('❌ No job detected on this page');
        if (sendResponse) sendResponse({ success: false, error: 'No job detected' });
        return;
      }

      showToast('🤖 AI analyzing job and applying...');

      // Send job to API for AI processing
      const response = await fetch(`${API_BASE}/api/job/analyze-and-apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobData),
      });

      if (response.ok) {
        const result = await response.json();
        
        // Auto-fill form if on application page
        if (detectApplicationForm()) {
          await fillApplicationForm(result.candidate_data);
        }
        
        showToast(`✅ Applied! Match score: ${result.match_score}%`);
        if (sendResponse) sendResponse({ success: true, score: result.match_score });
      } else {
        showToast('❌ Application failed. Open dashboard to apply.');
        if (sendResponse) sendResponse({ success: false });
      }
    } catch (e) {
      showToast('⚠️ Error. Try manual apply.');
      if (sendResponse) sendResponse({ success: false, error: e.message });
    }
  }

  // ── Auto-Fill Form ──
  async function handleFillForm(sendResponse) {
    try {
      const jobData = extractJobFromPage();
      const response = await fetch(`${API_BASE}/api/job/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobData),
      });
      
      if (response.ok) {
        const result = await response.json();
        await fillApplicationForm(result.candidate_data);
        showToast('✅ Form auto-filled!');
        if (sendResponse) sendResponse({ success: true });
      }
    } catch (e) {
      if (sendResponse) sendResponse({ success: false });
    }
  }

  // ── Generate Cover Letter ──
  async function handleGenerateCoverLetter(sendResponse) {
    try {
      const jobData = extractJobFromPage();
      const response = await fetch(`${API_BASE}/api/free-tools/cover-letter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: jobData.title,
          company: jobData.company,
          skills: jobData.skills || [],
        }),
      });
      
      if (response.ok) {
        const result = await response.json();
        showToast('✅ Cover letter copied to clipboard!');
        if (sendResponse) sendResponse({ success: true, letter: result.data.body });
      }
    } catch (e) {
      if (sendResponse) sendResponse({ success: false });
    }
  }

  // ── Extract job from page ──
  function extractJobFromPage() {
    const url = window.location.href;
    let job = { url, source: 'unknown', title: '', company: '', description: '', skills: [] };

    // LinkedIn
    if (url.includes('linkedin.com/jobs')) {
      job.source = 'linkedin';
      job.title = document.querySelector('.job-details-jobs-unified-top-card__job-title')?.textContent?.trim() ||
                  document.querySelector('h1')?.textContent?.trim() || '';
      job.company = document.querySelector('.job-details-jobs-unified-top-card__company-name')?.textContent?.trim() || '';
      job.description = document.querySelector('.jobs-description__content')?.textContent?.trim() || '';
      job.skills = [...document.querySelectorAll('.job-details-how-you-match__skills-item')].map(el => el.textContent.trim());
    }
    // Indeed
    else if (url.includes('indeed.com')) {
      job.source = 'indeed';
      job.title = document.querySelector('.jobsearch-JobInfoHeader-title')?.textContent?.trim() || '';
      job.company = document.querySelector('[data-company-name]')?.textContent?.trim() || '';
      job.description = document.getElementById('jobDescriptionText')?.textContent?.trim() || '';
    }
    // Glassdoor
    else if (url.includes('glassdoor.com')) {
      job.source = 'glassdoor';
      job.title = document.querySelector('.job-title')?.textContent?.trim() || '';
      job.company = document.querySelector('.employer-name')?.textContent?.trim() || '';
      job.description = document.querySelector('.jobDescriptionContent')?.textContent?.trim() || '';
    }
    // Bayt
    else if (url.includes('bayt.com')) {
      job.source = 'bayt';
      job.title = document.querySelector('.is-spaced')?.textContent?.trim() || '';
      job.company = document.querySelector('.t-small.u-mid')?.textContent?.trim() || '';
      job.description = document.querySelector('.card-content')?.textContent?.trim() || '';
    }
    // ZipRecruiter
    else if (url.includes('ziprecruiter.com')) {
      job.source = 'ziprecruiter';
      job.title = document.querySelector('.job_title')?.textContent?.trim() || '';
      job.company = document.querySelector('.company_name')?.textContent?.trim() || '';
      job.description = document.querySelector('.job_description')?.textContent?.trim() || '';
    }

    return job.title ? job : null;
  }

  // ── Detect application form ──
  function detectApplicationForm() {
    return !!(
      document.querySelector('input[name="name"]') ||
      document.querySelector('input[name="firstName"]') ||
      document.querySelector('input[name="email"]') ||
      document.querySelector('input[type="file"]') ||
      document.querySelector('textarea')
    );
  }

  // ── Fill application form ──
  async function fillApplicationForm(data) {
    if (!data) return;

    const fields = {
      'name': data.name || '',
      'firstName': data.first_name || '',
      'lastName': data.last_name || '',
      'email': data.email || '',
      'phone': data.phone || '',
      'location': data.location || '',
      'linkedin': data.linkedin_url || '',
      'website': data.website || '',
      'summary': data.summary || '',
    };

    // Fill text fields
    for (const [key, value] of Object.entries(fields)) {
      const input = document.querySelector(`input[name="${key}"], input[id*="${key}"], textarea[name="${key}"], textarea[id*="${key}"]`);
      if (input && value) {
        input.value = value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    // Try to attach resume file if upload input exists
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput && data.cv_url) {
      try {
        const response = await fetch(data.cv_url);
        const blob = await response.blob();
        const file = new File([blob], 'resume.pdf', { type: 'application/pdf' });
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
      } catch (e) {
        console.log('[JobHunt Pro] Could not attach resume file');
      }
    }
  }

  // ── Toast notification ──
  function showToast(message) {
    const existing = document.getElementById('jh-pro-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'jh-pro-toast';
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed; bottom: 80px; right: 20px; z-index: 9999999;
      background: #0a0a1a; color: #e0e0e0; padding: 12px 24px;
      border-radius: 8px; font-size: 14px; font-family: system-ui;
      border: 1px solid #00f0ff44; box-shadow: 0 4px 20px #00000088;
      animation: jhToastIn 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  // ── Add toast animation ──
  const style = document.createElement('style');
  style.textContent = `
    @keyframes jhToastIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;
  document.head.appendChild(style);

  // ── Inject button after page load ──
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectFloatingButton);
  } else {
    injectFloatingButton();
  }
})();
