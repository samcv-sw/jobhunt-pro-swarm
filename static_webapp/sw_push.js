/**
 * JobHunt Pro - Service Worker for Mobile & Desktop Web Push Notifications
 */

self.addEventListener('install', (event) => {
  console.log('[JobHunt Pro SW] Service Worker Installed');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[JobHunt Pro SW] Service Worker Activated');
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let data = { title: 'JobHunt Pro Alert', body: 'New high-match job opportunity found!' };
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/badge-72.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/dashboard'
    },
    actions: [
      { action: 'open', title: 'View Match 🚀' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'open' || !event.action) {
    const targetUrl = event.notification.data ? event.notification.data.url : '/dashboard';
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
        for (let client of clientList) {
          if (client.url === targetUrl && 'focus' in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
    );
  }
});
