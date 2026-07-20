const CACHE_NAME = 'jobhunt-pro-v3-dynamic';
const OFFLINE_URL = '/offline.html';
const STATIC_ASSETS = [
  '/',
  '/en/',
  OFFLINE_URL,
  '/static/css/index.css',
  '/static/css/cyberpunk.css',
  '/static/js/cyberpunk.js',
  '/static/manifest.json',
  '/static/favicon.png'
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
  if (request.url.includes('/api/') || request.url.includes('/ws/')) {
    event.respondWith(fetch(request));
    return;
  }
  if (!request.url.startsWith(self.location.origin)) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const fetchPromise = fetch(request).then((networkResponse) => {
          caches.open(CACHE_NAME).then((cache) => cache.put(request, networkResponse.clone()));
          return networkResponse;
        }).catch(() => cachedResponse);
        return cachedResponse || fetchPromise;
      })
    );
    return;
  }
  if (request.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(request).then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        return response;
      }).catch(() => {
        return caches.match(request).then((cached) => cached || caches.match(OFFLINE_URL));
      })
    );
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
