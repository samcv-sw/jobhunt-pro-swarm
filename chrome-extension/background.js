// JobHunt Pro - Background Service Worker
const API_BASE = 'https://jhfguf.pythonanywhere.com';
const ALARM_NAME = 'statsUpdate';

// ── Install ──
chrome.runtime.onInstalled.addListener(() => {
  console.log('[JobHunt Pro] Extension installed');
  
  // Set up periodic stats update
  chrome.alarms.create(ALARM_NAME, { periodInMinutes: 5 });
  
  // Open welcome page on install
  chrome.tabs.create({ url: `${API_BASE}?utm_source=chrome-extension` });
});

// ── Alarm handler ──
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === ALARM_NAME) {
    await updateStats();
  }
});

// ── Message handlers ──
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getStats') {
    chrome.storage.local.get(['stats'], (data) => {
      sendResponse(data.stats || getDefaultStats());
    });
    return true; // async response
  }
  
  if (request.action === 'updateStats') {
    updateStats().then(sendResponse);
    return true;
  }

  if (request.action === 'openDashboard') {
    chrome.tabs.create({ url: API_BASE + '/user-dashboard' });
    sendResponse({ success: true });
  }
});

// ── Stats management ──
async function updateStats() {
  try {
    const data = await chrome.storage.local.get([STORAGE_KEY]);
    if (!data[STORAGE_KEY]) return getDefaultStats();

    const response = await fetch(`${API_BASE}/api/user/stats`, {
      headers: { 'Authorization': `Bearer ${data[STORAGE_KEY].token}` }
    });
    
    if (response.ok) {
      const json = await response.json();
      const stats = {
        apps: json.total_applications || 0,
        matchRate: json.match_rate || 0,
        coverLetters: json.cover_letters || 0,
        timeSaved: Math.round((json.applications_sent || 0) * 5 / 60)
      };
      await chrome.storage.local.set({ stats });
      return stats;
    }
  } catch (e) {
    console.error('[JobHunt Pro] Stats update failed:', e);
  }
  return getDefaultStats();
}

function getDefaultStats() {
  return { apps: 0, matchRate: 0, coverLetters: 0, timeSaved: 0 };
}

const STORAGE_KEY = 'jobhunt_pro_auth';
