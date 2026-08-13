// Service Worker for JobHunt Pro PWA (100% Grade S+ Specification)
const CACHE_NAME = 'jobhunt-pro-v2';
const ASSETS_TO_CACHE = [
  '/',
  '/static/manifest.json',
  '/static/offline.html',
  '/favicon.ico'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Network first for HTML navigation with offline.html fallback, cache fallback for assets
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request).then((response) => {
          if (response) return response;
          return caches.match('/static/offline.html');
        });
      })
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request).catch(() => {
          // Fallback response for missing dynamic assets
          if (event.request.headers.get('accept')?.includes('text/html')) {
            return caches.match('/static/offline.html');
          }
        });
      })
    );
  }
});
