const APP_SHELL_CACHE = "guardian-shell-v2";
const RUNTIME_CACHE = "guardian-runtime-v2";
const TILE_CACHE = "guardian-map-tiles-v1";
const PRECACHE_URLS = [
  "/",
  "/manifest.webmanifest",
  "/icons/icon-192.svg",
  "/icons/icon-512.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(APP_SHELL_CACHE).then((cache) => cache.addAll(PRECACHE_URLS)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== APP_SHELL_CACHE && key !== RUNTIME_CACHE && key !== TILE_CACHE)
          .map((key) => caches.delete(key)),
      ),
    ),
  );
  self.clients.claim();
});

async function networkFirst(request) {
  const runtimeCache = await caches.open(RUNTIME_CACHE);
  try {
    const response = await fetch(request);
    if (response && (response.ok || response.type === "opaque")) {
      runtimeCache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await runtimeCache.match(request);
    if (cached) {
      return cached;
    }
    if (request.mode === "navigate") {
      return (await caches.match("/")) || Response.error();
    }
    return Response.error();
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  const response = await fetch(request);
  if (response && (response.ok || response.type === "opaque")) {
    const runtimeCache = await caches.open(RUNTIME_CACHE);
    runtimeCache.put(request, response.clone());
  }
  return response;
}

async function tileCacheFirst(request) {
  const tileCache = await caches.open(TILE_CACHE);
  const cached = await tileCache.match(request);
  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response && (response.ok || response.type === "opaque")) {
      tileCache.put(request, response.clone());
    }
    return response;
  } catch {
    return (await tileCache.match(request)) || Response.error();
  }
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);
  const isApiRequest = url.pathname.includes("/api/v1/");
  const isSameOrigin = url.origin === self.location.origin;
  const isTileRequest =
    url.hostname === "tile.openstreetmap.org" ||
    url.hostname.endsWith(".tile.openstreetmap.org");

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request));
    return;
  }

  if (isApiRequest) {
    event.respondWith(networkFirst(request));
    return;
  }

  if (isTileRequest) {
    event.respondWith(tileCacheFirst(request));
    return;
  }

  if (isSameOrigin) {
    event.respondWith(cacheFirst(request));
  }
});
