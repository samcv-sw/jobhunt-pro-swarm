// JobHunt Pro - Auto Apply Extension Background Worker
// Tracks application stats, handles cross-tab messaging

const STATS_KEY = 'jh_apply_stats';

// Initialize stats on install
chrome.runtime.onInstalled.addListener(async () => {
  const existing = await chrome.storage.local.get(STATS_KEY);
  if (!existing[STATS_KEY]) {
    const today = new Date().toISOString().split('T')[0];
    await chrome.storage.local.set({
      [STATS_KEY]: {
        total: 0,
        today: 0,
        todayDate: today,
        successful: 0,
        failed: 0,
        history: []
      }
    });
  }
});

// Listen for application submissions from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'APPLICATION_SUBMITTED') {
    handleApplicationSubmitted(message.data);
    sendResponse({ success: true });
  }
  if (message.type === 'GET_STATS') {
    getStats().then(stats => sendResponse(stats));
    return true; // async response
  }
  if (message.type === 'GET_PROFILE') {
    chrome.storage.local.get('jh_profile').then(data => {
      sendResponse(data.jh_profile || null);
    });
    return true;
  }
});

async function handleApplicationSubmitted(data) {
  const stored = await chrome.storage.local.get(STATS_KEY);
  const stats = stored[STATS_KEY] || { total: 0, today: 0, todayDate: '', successful: 0, failed: 0, history: [] };

  const today = new Date().toISOString().split('T')[0];
  const isNewDay = stats.todayDate !== today;

  stats.total = (stats.total || 0) + 1;
  stats.today = isNewDay ? 1 : (stats.today || 0) + 1;
  stats.todayDate = today;

  if (data.success) {
    stats.successful = (stats.successful || 0) + 1;
  } else {
    stats.failed = (stats.failed || 0) + 1;
  }

  // Keep last 50 in history
  stats.history = stats.history || [];
  stats.history.unshift({
    url: data.url,
    company: data.company || 'Unknown',
    title: data.title || 'Unknown',
    success: data.success,
    timestamp: Date.now()
  });
  if (stats.history.length > 50) stats.history = stats.history.slice(0, 50);

  await chrome.storage.local.set({ [STATS_KEY]: stats });
}

async function getStats() {
  const stored = await chrome.storage.local.get(STATS_KEY);
  const stats = stored[STATS_KEY] || { total: 0, today: 0, todayDate: '', successful: 0, failed: 0, history: [] };

  // Reset today count if new day
  const today = new Date().toISOString().split('T')[0];
  if (stats.todayDate !== today) {
    stats.today = 0;
    stats.todayDate = today;
    await chrome.storage.local.set({ [STATS_KEY]: stats });
  }

  return stats;
}
