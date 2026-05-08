const CACHE_NAME = "vigil-dashboard-v1";
const ASSETS = [
  "/",
  "/devices",
  "/alerts",
  "/analytics",
  "/manifest.json",
];

// Install: cache basic assets
self.addEventListener("install", (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener("activate", (event: ExtendableEvent) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: network-first with cache fallback for pages
self.addEventListener("fetch", (event: FetchEvent) => {
  const { request } = event;

  // Only handle GET requests
  if (request.method !== "GET") return;

  // Don't cache API calls
  if (request.url.includes("192.168.50.30")) {
    event.respondWith(fetch(request));
    return;
  }

  // Try network first, fall back to cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache successful responses
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(request, clone);
        });
        return response;
      })
      .catch(() => {
        return caches.match(request).then((cached) => {
          return (
            cached ||
            new Response("Offline", {
              status: 503,
              statusText: "Service Unavailable",
            })
          );
        });
      })
  );
});

// Type extensions for ServiceWorkerGlobalScope
interface ExtendableEvent extends Event {
  waitUntil(promise: Promise<unknown>): void;
}

interface FetchEvent extends Event {
  request: Request;
  respondWith(response: Promise<Response> | Response): void;
}
