const CACHE_NAME = 'jobhunt-pro-v2-dynamic';
const STATIC_ASSETS = [
  '/',
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
      return cache.addAll(STATIC_ASSETS);
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME).map(name => caches.delete(name))
      );
    })
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  
  // API calls and WebSockets should bypass cache completely
  if (request.url.includes('/api/') || request.url.includes('/ws/')) {
    event.respondWith(fetch(request));
    return;
  }

  // Cross-Origin CDNs (Fonts, Alpine, ChartJS) -> Stale-While-Revalidate
  if (!request.url.startsWith(self.location.origin)) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const fetchPromise = fetch(request).then(networkResponse => {
          caches.open(CACHE_NAME).then(cache => cache.put(request, networkResponse.clone()));
          return networkResponse;
        }).catch(() => cachedResponse);
        return cachedResponse || fetchPromise;
      })
    );
    return;
  }

  // Network-First for HTML/Dashboard
  if (request.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(request).then(response => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        return response;
      }).catch(() => {
        return caches.match(request).then(cached => cached || caches.match('/'));
      })
    );
    return;
  }

  // Cache-First for static assets (CSS, JS, Images)
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse;
      
      return fetch(request).then(networkResponse => {
        const copy = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        return networkResponse;
      });
    })
  );
});
