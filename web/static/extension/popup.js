// JobHunt Pro - Popup Script
// Handles popup UI, stats display, and navigation

document.addEventListener('DOMContentLoaded', async () => {
  await loadStats();
  await loadProfileStatus();
  await loadRecentActivity();

  // Button handlers
  document.getElementById('btn-configure').addEventListener('click', openProfileTab);
  document.getElementById('btn-open-dashboard').addEventListener('click', openDashboard);
});

async function loadStats() {
  try {
    const stats = await chrome.runtime.sendMessage({ type: 'GET_STATS' });
    const total = stats.total || 0;
    const today = stats.today || 0;
    const successful = stats.successful || 0;

    document.getElementById('stat-today').textContent = today;
    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-rate').textContent = total > 0 ? Math.round((successful / total) * 100) + '%' : '-';
  } catch (e) {
    document.getElementById('stat-today').textContent = '0';
    document.getElementById('stat-total').textContent = '0';
    document.getElementById('stat-rate').textContent = '-';
  }
}

async function loadProfileStatus() {
  try {
    const stored = await chrome.storage.local.get('jh_profile');
    const profile = stored.jh_profile;
    const dot = document.querySelector('.status-dot');
    const text = document.getElementById('profile-text');

    if (profile && profile.name) {
      dot.className = 'status-dot active';
      text.textContent = `✓ Profile: ${profile.name} | ${profile.email || 'No email'}`;
    } else {
      dot.className = 'status-dot inactive';
      text.textContent = 'No profile set — click Configure to set up';
    }
  } catch (e) {
    document.getElementById('profile-text').textContent = 'Error loading profile';
  }
}

async function loadRecentActivity() {
  try {
    const stored = await chrome.storage.local.get('jh_apply_stats');
    const stats = stored.jh_apply_stats || {};
    const history = stats.history || [];

    const container = document.getElementById('activity-list');
    if (history.length === 0) {
      container.innerHTML = '<div class="empty-state">No applications yet — visit a job site!</div>';
      return;
    }

    const recent = history.slice(0, 5);
    container.innerHTML = recent.map(item => {
      const icon = item.success ? '✅' : '❌';
      const time = formatTime(item.timestamp);
      return `
        <div class="activity-item">
          <div class="activity-icon fill">${icon}</div>
          <div class="activity-info">
            <div class="activity-company">${escapeHtml(item.company)}</div>
            <div class="activity-time">${escapeHtml(item.title)} · ${time}</div>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    document.getElementById('activity-list').innerHTML =
      '<div class="empty-state">Error loading activity</div>';
  }
}

function openProfileTab() {
  // Open the extension options / trigger the content script settings modal
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { type: 'OPEN_PROFILE' }).catch(() => {
        // If content script not listening, open options page
        chrome.runtime.openOptionsPage
          ? chrome.runtime.openOptionsPage()
          : chrome.tabs.create({ url: 'popup.html?settings=1' });
      });
    }
  });
}

function openDashboard() {
  chrome.tabs.create({ url: 'https://jhfguf.pythonanywhere.com/user-dashboard' });
}

function formatTime(timestamp) {
  const now = Date.now();
  const diff = now - timestamp;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Handle settings mode (when opened directly)
if (window.location.search.includes('settings=1')) {
  document.addEventListener('DOMContentLoaded', () => {
    document.body.innerHTML = `
      <div style="width:380px;padding:20px;font-family:'Inter',sans-serif;background:#0a0a14;color:#e2e8f0;min-height:100vh;">
        <h2 style="margin-bottom:16px;">⚡ Profile Settings</h2>
        <form id="settings-form">
          <label style="display:block;margin-bottom:12px;font-size:12px;color:#94a3b8;">Full Name
            <input type="text" id="s-name" style="width:100%;padding:8px;margin-top:4px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#e2e8f0;font-size:13px;">
          </label>
          <label style="display:block;margin-bottom:12px;font-size:12px;color:#94a3b8;">Email
            <input type="email" id="s-email" style="width:100%;padding:8px;margin-top:4px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#e2e8f0;font-size:13px;">
          </label>
          <label style="display:block;margin-bottom:12px;font-size:12px;color:#94a3b8;">Phone
            <input type="tel" id="s-phone" style="width:100%;padding:8px;margin-top:4px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#e2e8f0;font-size:13px;">
          </label>
          <label style="display:block;margin-bottom:16px;font-size:12px;color:#94a3b8;">Resume File Name
            <input type="text" id="s-resume" style="width:100%;padding:8px;margin-top:4px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#e2e8f0;font-size:13px;">
          </label>
          <button type="submit" style="width:100%;padding:10px;background:#3b82f6;color:#fff;border:none;border-radius:10px;font-weight:600;cursor:pointer;">Save Profile</button>
        </form>
      </div>
    `;

    // Load existing profile
    chrome.storage.local.get('jh_profile', (data) => {
      const p = data.jh_profile || {};
      document.getElementById('s-name').value = p.name || '';
      document.getElementById('s-email').value = p.email || '';
      document.getElementById('s-phone').value = p.phone || '';
      document.getElementById('s-resume').value = p.resumeFileName || '';
    });

    document.getElementById('settings-form').addEventListener('submit', (e) => {
      e.preventDefault();
      const profile = {
        name: document.getElementById('s-name').value.trim(),
        email: document.getElementById('s-email').value.trim(),
        phone: document.getElementById('s-phone').value.trim(),
        resumeFileName: document.getElementById('s-resume').value.trim(),
        updatedAt: Date.now()
      };
      chrome.storage.local.set({ jh_profile: profile }, () => {
        window.close();
      });
    });
  });
}
