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

// ── LinkedIn Connector (send connection request to current profile) ──
document.getElementById('btnLinkedInConnect').addEventListener('click', async () => {
  const btn = document.getElementById('btnLinkedInConnect');
  btn.disabled = true;
  btn.textContent = '⏳ Connecting...';
  
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.tabs.sendMessage(tab.id, { action: 'linkedInConnect' }, (response) => {
    btn.textContent = response?.success ? '✅ Sent!' : '❌ Failed';
    setTimeout(() => { btn.disabled = false; btn.textContent = '🔗 LinkedIn Connect'; }, 2000);
  });
});

// ── LinkedIn Bulk Connector ──
document.getElementById('btnLinkedInConnector').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.tabs.sendMessage(tab.id, { action: 'linkedInConnector' });
});

document.getElementById('btnCheckATS').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/free-tools` });
});

document.getElementById('btnDashboard').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/user-dashboard` });
});

document.getElementById('btnSettings').addEventListener('click', () => {
  const panel = document.getElementById('settingsPanel');
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  if (panel.style.display === 'block') {
    chrome.storage.local.get(['blacklist', 'byok'], (data) => {
      if (data.blacklist) document.getElementById('blacklistInput').value = data.blacklist.join(', ');
      if (data.byok) {
        document.getElementById('byokProvider').value = data.byok.provider || 'groq';
        document.getElementById('byokInput').value = data.byok.key || '';
      }
    });
  }
});

// ── BYOK Save ──
document.getElementById('btnSaveByok').addEventListener('click', () => {
  const provider = document.getElementById('byokProvider').value;
  const key = document.getElementById('byokInput').value.trim();
  if (key) {
    chrome.storage.local.set({ byok: { provider, key } }, () => {
      const btn = document.getElementById('btnSaveByok');
      btn.textContent = '✅ Saved!';
      setTimeout(() => { btn.textContent = 'Save API Key'; }, 1500);
    });
  }
});

document.getElementById('btnSaveSettings').addEventListener('click', () => {
  const input = document.getElementById('blacklistInput').value;
  const blacklist = input.split(',').map(s => s.trim().toLowerCase()).filter(s => s);
  chrome.storage.local.set({ blacklist }, () => {
    const btn = document.getElementById('btnSaveSettings');
    btn.textContent = '✅ Saved';
    setTimeout(() => { btn.textContent = 'Save Blacklist'; }, 1500);
  });
});

// Follow-ups panel toggling (we can reuse btnCampaign or make a new one)
// I will just display followups inside the followupsPanel automatically
function loadFollowups() {
  chrome.storage.local.get(['followups'], (data) => {
    if (data.followups && data.followups.length > 0) {
      document.getElementById('followupsPanel').style.display = 'block';
      const list = document.getElementById('followupsList');
      list.innerHTML = '';
      data.followups.slice(-5).reverse().forEach(f => {
        const div = document.createElement('div');
        div.style.padding = '6px';
        div.style.background = '#000';
        div.style.border = '1px solid #333';
        div.style.borderRadius = '4px';
        div.innerHTML = `<strong>${f.company}</strong><br/>${f.message}`;
        list.appendChild(div);
      });
    }
  });
}
loadFollowups();

document.getElementById('btnBulkApply').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/new-campaign` });
});

document.getElementById('btnCampaign').addEventListener('click', () => {
  chrome.tabs.create({ url: `${API_BASE}/campaigns` });
});
