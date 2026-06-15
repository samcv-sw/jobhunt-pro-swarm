// JobHunt Pro - Chrome Extension Popup
const API_BASE = 'https://jhfguf.pythonanywhere.com';
const STORAGE_KEY = 'jobhunt_pro_auth';

// ── Init ──
document.addEventListener('DOMContentLoaded', async () => {
  const data = await chrome.storage.local.get([STORAGE_KEY, 'stats']);
  
  if (data[STORAGE_KEY]) {
    document.getElementById('statusBar').textContent = '🟢 Connected';
    document.getElementById('statusBar').className = 'status connected';
    loadStats();
  } else {
    document.getElementById('statusBar').textContent = '🔌 Click to connect your account';
    document.getElementById('statusBar').style.cursor = 'pointer';
    document.getElementById('statusBar').addEventListener('click', () => {
      chrome.tabs.create({ url: `${API_BASE}/register` });
    });
  }

  if (data.stats) updateStats(data.stats);
});

// ── Stats ──
function loadStats() {
  chrome.runtime.sendMessage({ action: 'getStats' }, (response) => {
    if (response && !response.error) updateStats(response);
  });
}

function updateStats(stats) {
  document.getElementById('appsToday').textContent = stats.apps || 0;
  document.getElementById('matchRate').textContent = (stats.matchRate || 0) + '%';
  document.getElementById('coverLetters').textContent = stats.coverLetters || 0;
  document.getElementById('timeSaved').textContent = (stats.timeSaved || 0) + 'h';
}

// ── Buttons ──
document.getElementById('btnAutoApply').addEventListener('click', async () => {
  const btn = document.getElementById('btnAutoApply');
  btn.disabled = true;
  btn.textContent = '⏳ Applying...';

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.tabs.sendMessage(tab.id, { action: 'autoApply' }, (response) => {
    if (response?.success) {
      btn.textContent = '✅ Applied!';
      loadStats();
    } else {
      btn.textContent = '❌ Failed - Try Again';
    }
    setTimeout(() => { btn.disabled = false; btn.textContent = '🚀 Auto-Apply to This Job'; }, 2000);
  });
});

document.getElementById('btnFillForm').addEventListener('click', async () => {
  const btn = document.getElementById('btnFillForm');
  btn.disabled = true;
  btn.textContent = '⏳ Filling...';
  
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.tabs.sendMessage(tab.id, { action: 'fillForm' }, () => {
    btn.textContent = '✅ Form Filled!';
    setTimeout(() => { btn.disabled = false; btn.textContent = '📝 Auto-Fill Application Form'; }, 1500);
  });
});

document.getElementById('btnGenerateCL').addEventListener('click', async () => {
  const btn = document.getElementById('btnGenerateCL');
  btn.disabled = true;
  btn.textContent = '⏳ Generating...';
  
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.tabs.sendMessage(tab.id, { action: 'generateCoverLetter' }, (response) => {
    if (response?.letter) {
      navigator.clipboard.writeText(response.letter);
      btn.textContent = '✅ Copied!';
    }
    setTimeout(() => { btn.disabled = false; btn.textContent = '✍️ Generate Cover Letter'; }, 1500);
  });
});

document.getElementById('btnCheckATS').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/free-tools` });
});

document.getElementById('btnDashboard').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/user-dashboard` });
});

document.getElementById('btnSettings').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/settings` });
});

document.getElementById('btnBulkApply').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/new-campaign` });
});

document.getElementById('btnCampaign').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/campaigns` });
});
