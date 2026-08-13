const CACHE_NAME = 'jobhunt-pro-v5-enterprise';
const OFFLINE_URL = '/static/offline.html';
const STATIC_ASSETS = [
  '/',
  '/en/',
  '/dashboard',
  OFFLINE_URL,
  '/static/css/index.css',
  '/static/css/cyberpunk.css',
  '/static/js/cyberpunk.js',
  '/static/manifest.json',
  '/static/favicon.png',
  'https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Tajawal:wght@400;500;700&display=swap'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.allSettled(
        STATIC_ASSETS.map((url) => cache.add(url).catch(() => {}))
      );
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.allSettled(
        cacheNames.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
      ).then(() => self.clients.claim());
    })
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.mode === 'navigate' || (request.headers.get('accept') && request.headers.get('accept').includes('text/html'))) {
    event.respondWith(
      fetch(request).catch(() => {
        return caches.match(OFFLINE_URL).then((offlineRes) => {
          if (offlineRes) return offlineRes;
          return caches.match('/').then((rootRes) => {
            return rootRes || new Response('<h1>Offline — JobHunt Pro</h1><p>Network connection unavailable.</p>', {
              headers: { 'Content-Type': 'text/html' }
            });
          });
        });
      })
    );
    return;
  }
  if (request.url.includes('/api/') || request.url.includes('/ws/')) {
    event.respondWith(fetch(request));
    return;
  }
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse;
      return fetch(request).then((networkResponse) => {
        const copy = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        return networkResponse;
      });
    })
  );
});

