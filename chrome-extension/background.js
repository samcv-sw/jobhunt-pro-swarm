// JobHunt Pro v2 — Background Service Worker
// Simplified: NO chrome.debugger — uses MAIN world click via content.js
const API_BASE = 'https://jhfguf.pythonanywhere.com';
const ALARM_NAME = 'statsUpdate';
const STORAGE_KEY = 'jobhunt_pro_auth';

// ── Install ──
chrome.runtime.onInstalled.addListener(() => {
  console.log('[JHPro] v2.0 installed — stealth mode active');
  chrome.alarms.create(ALARM_NAME, { periodInMinutes: 5 });
  chrome.tabs.create({ url: `${API_BASE}?utm_source=chrome-extension-v2` });
});

// ── Alarm: update stats ──
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === ALARM_NAME) await updateStats();
});

// ── Message routing ──
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // Popup stats
  if (request.action === 'getStats') {
    chrome.storage.local.get(['stats'], (data) => {
      sendResponse(data.stats || getDefaultStats());
    });
    return true;
  }
  
  if (request.action === 'updateStats') {
    updateStats().then(sendResponse);
    return true;
  }

  if (request.action === 'openDashboard') {
    chrome.tabs.create({ url: API_BASE + '/user-dashboard' });
    sendResponse({ success: true });
    return;
  }

  if (request.action === 'openCampaign') {
    chrome.tabs.create({ url: API_BASE + '/new-campaign' });
    sendResponse({ success: true });
    return;
  }

  // ── Swarm state reporting ──
  if (request.type === 'REPORT_STATE') {
    console.log(`[CmdCenter] Tab ${sender.tab.id}: ${request.status} (${request.timeActive}ms)`);
    
    // Smart skip: if >45s on one job, abort
    if (request.timeActive > 45000) {
      console.warn(`[CmdCenter] Smart skip: tab ${sender.tab.id}`);
      try {
        chrome.tabs.sendMessage(sender.tab.id, { type: 'SMART_SKIP', reason: 'timeout_45s' });
      } catch(e) {}
    }
    sendResponse({ success: true });
    return;
  }

  if (request.type === 'CAPTCHA_DETECTED') {
    console.warn(`[CmdCenter] 🚨 CAPTCHA in tab ${sender.tab.id}`);
    try {
      chrome.tabs.sendMessage(sender.tab.id, { type: 'GLOBAL_HALT', reason: 'captcha_intervention' });
    } catch(e) {}
    sendResponse({ success: true });
    return;
  }

  // ── API proxy (keeps API key server-side) ──
  if (request.action === 'api_proxy') {
    proxyAPI(request.endpoint, request.method, request.body)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (request.action === 'NOTIFICATION') {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: request.title || 'JobHunt Pro',
      message: request.message || ''
    });
    sendResponse({ success: true });
    return;
  }

  // ── LinkedIn Connector ──
  if (request.action === 'send_connection') {
    chrome.tabs.create({
      url: `https://www.linkedin.com/in/${request.liProfileId}/`,
      active: false
    }, (tab) => {
      // Content script will auto-detect and send connection
      setTimeout(() => {
        try {
          chrome.tabs.sendMessage(tab.id, {
            type: 'CONNECT_REQUEST',
            profileId: request.liProfileId,
            message: request.message
          });
        } catch(e) {}
      }, 3000);
    });
    sendResponse({ success: true });
    return;
  }

  if (request.action === 'check_robots') {
    checkRobotsTxt(request.url).then(allowed => sendResponse({ allowed }));
    return true;
  }

  // Default response
  sendResponse({ success: false, error: 'unknown_action' });
});

// ── API proxy ──
async function proxyAPI(endpoint, method = 'GET', body = null) {
  const data = await chrome.storage.local.get([STORAGE_KEY]);
  const token = data[STORAGE_KEY]?.token || '';
  
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);
  
  const response = await fetch(`${API_BASE}${endpoint}`, options);
  const json = await response.json();
  return { success: response.ok, data: json, status: response.status };
}

// ── Stats ──
async function updateStats() {
  try {
    const data = await chrome.storage.local.get([STORAGE_KEY]);
    if (!data[STORAGE_KEY]) return getDefaultStats();

    const resp = await proxyAPI('/api/user/stats');
    if (resp.success) {
      const d = resp.data;
      const stats = {
        apps: d.total_applications || 0,
        matchRate: d.match_rate || 0,
        coverLetters: d.cover_letters || 0,
        timeSaved: Math.round((d.applications_sent || 0) * 5 / 60)
      };
      await chrome.storage.local.set({ stats });
      return stats;
    }
  } catch (e) {
    console.error('[JHPro] Stats error:', e);
  }
  return getDefaultStats();
}

function getDefaultStats() {
  return { apps: 0, matchRate: 0, coverLetters: 0, timeSaved: 0 };
}

// ── Compliance: robots.txt ──
const robotsCache = {};

async function checkRobotsTxt(targetUrl) {
  try {
    const url = new URL(targetUrl);
    const robotsUrl = `${url.origin}/robots.txt`;
    
    if (robotsCache[robotsUrl] && (Date.now() - robotsCache[robotsUrl].timestamp < 3600000)) {
      return isAllowedByRobots(url.pathname, robotsCache[robotsUrl].rules);
    }
    
    const resp = await fetch(robotsUrl);
    if (!resp.ok) return true; // If 404, assume allowed
    
    const text = await resp.text();
    const rules = parseRobotsTxt(text);
    robotsCache[robotsUrl] = { timestamp: Date.now(), rules };
    return isAllowedByRobots(url.pathname, rules);
  } catch (e) {
    return true; // Fallback to allowed if fetch fails
  }
}

function parseRobotsTxt(text) {
  const rules = { allow: [], disallow: [] };
  let isUserAgentMatch = false;
  
  const lines = text.split('\n');
  for (const line of lines) {
    const cleanLine = line.split('#')[0].trim();
    if (!cleanLine) continue;
    
    const [key, ...valueParts] = cleanLine.split(':');
    const value = valueParts.join(':').trim();
    
    if (key.toLowerCase() === 'user-agent') {
      isUserAgentMatch = value === '*' || value.toLowerCase().includes('jobhunt');
    } else if (isUserAgentMatch) {
      if (key.toLowerCase() === 'disallow' && value) rules.disallow.push(value);
      if (key.toLowerCase() === 'allow' && value) rules.allow.push(value);
    }
  }
  return rules;
}

function isAllowedByRobots(path, rules) {
  for (const allow of rules.allow) {
    if (path.startsWith(allow)) return true;
  }
  for (const disallow of rules.disallow) {
    if (path.startsWith(disallow)) return false;
  }
  return true;
}
