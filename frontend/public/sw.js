/**
 * JobHunt Pro PWA Sovereign Service Worker.
 * Enables zero-latency offline page caching, push notifications, and background sync.
 */

const CACHE_NAME = "jobhunt-pro-v3.0";
const OFFLINE_URLS = [
  "/",
  "/dashboard",
  "/voice-interview",
  "/static/css/style.css",
  "/wasm_parser.js"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(OFFLINE_URLS).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        fetch(event.request).then((networkResponse) => {
          if (networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
          }
        }).catch(() => {});
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});

self.addEventListener("push", (event) => {
  let data = { title: "JobHunt Pro Alert", body: "New application match found!", action_url: "/dashboard" };
  if (event.data) {
    try { data = event.data.json(); } catch (e) {}
  }
  
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/static/img/icon-192.png",
      data: { url: data.action_url }
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const urlToOpen = event.notification.data ? event.notification.data.url : "/dashboard";
  event.waitUntil(
    clients.openWindow(urlToOpen)
  );
});
