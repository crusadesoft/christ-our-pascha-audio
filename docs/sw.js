/* Service worker.
   Shell is precached so the app opens offline. Audio is NOT precached -- the
   whole recording is ~351 MB; tracks are cached only after they have been
   played, or when explicitly downloaded from the UI. */
const VER   = 'pascha-v602e38b7b9';
const SHELL = 'shell-' + VER;
const AUDIO = 'audio-' + VER;
const PRECACHE = [
  './', './index.html', './about.html', './subscribe.html',
  './style.css', './cover.jpg', './data.enc', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    // individually, so one failure does not abort the whole install
    await Promise.all(PRECACHE.map(u => c.add(u).catch(() => {})));
    self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keep = new Set([SHELL, AUDIO]);
    for (const k of await caches.keys()) if (!keep.has(k)) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  // Audio: cache-first, and never partially cache. Range requests are passed
  // to the network untouched -- storing a 206 would poison the cache with a
  // fragment that later reads would treat as the whole file.
  if (url.pathname.includes('/audio/')) {
    if (req.headers.has('range')) return;
    e.respondWith((async () => {
      const c = await caches.open(AUDIO);
      const hit = await c.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok && res.status === 200) c.put(req, res.clone());
      return res;
    })());
    return;
  }

  // Shell: network-first so a redeploy is picked up, cache as fallback.
  e.respondWith((async () => {
    try {
      const res = await fetch(req);
      if (res.ok) (await caches.open(SHELL)).put(req, res.clone());
      return res;
    } catch (err) {
      const hit = await caches.match(req);
      if (hit) return hit;
      throw err;
    }
  })());
});

// UI asks for a track to be stored, or reports what is stored
self.addEventListener('message', e => {
  const { type, urls } = e.data || {};
  if (type === 'cache-audio') {
    e.waitUntil((async () => {
      const c = await caches.open(AUDIO);
      let done = 0;
      for (const u of urls) {
        try { await c.add(u); } catch (err) {}
        done++;
        e.source && e.source.postMessage({type: 'cache-progress', done, total: urls.length});
      }
      e.source && e.source.postMessage({type: 'cache-done', total: urls.length});
    })());
  }
  if (type === 'cache-status') {
    e.waitUntil((async () => {
      const c = await caches.open(AUDIO);
      const keys = await c.keys();
      e.source && e.source.postMessage({type: 'cache-status', count: keys.length});
    })());
  }
  if (type === 'cache-clear') {
    e.waitUntil((async () => {
      await caches.delete(AUDIO);
      e.source && e.source.postMessage({type: 'cache-status', count: 0});
    })());
  }
});
