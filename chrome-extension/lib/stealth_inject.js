// JobHunt Pro v2 — Stealth Inject
// Runs at document_start in world:MAIN — spoofs automation flags
// BEFORE any page JS loads. Datadome/Cloudflare see a 100% real browser.

(function() {
  'use strict';
  
  // ── 1. Kill navigator.webdriver ──
  delete navigator.__proto__.webdriver;
  Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true
  });

  // ── 2. Override cdc_adoQpoasnfa76pfcZLmcfl (Cloudflare's secret detection var) ──
  const cdcKey = Object.keys(window).find(k => k.startsWith('cdc_'));
  if (cdcKey) {
    try { delete window[cdcKey]; } catch(e) {}
    Object.defineProperty(window, cdcKey, {
      get: () => undefined,
      set: () => {},
      configurable: true
    });
  }

  // ── 3. Override chrome.runtime presence in MAIN world ──
  // Some sites check if chrome.runtime exists (CDP extension detection)
  if (window.chrome && window.chrome.runtime) {
    const origChrome = window.chrome;
    window.chrome = new Proxy(origChrome, {
      get(target, prop) {
        if (prop === 'runtime') {
          return {
            id: undefined,
            getManifest: () => ({}),
            connect: () => null,
            sendMessage: () => {}
          };
        }
        return target[prop];
      }
    });
  }

  // ── 4. Canvas fingerprint spoofing ──
  const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
  HTMLCanvasElement.prototype.toDataURL = function(type) {
    const isFingerprint = (this.width === 16 || this.width === 32) &&
                          (this.height === 16 || this.height === 32);
    if (isFingerprint) {
      // Return a slightly noised version
      const ctx = this.getContext('2d');
      if (ctx) {
        ctx.fillStyle = 'rgba(0,0,0,0.003)';
        ctx.fillRect(0, 0, 1, 1);
      }
    }
    return origToDataURL.apply(this, arguments);
  };

  // ── 5. WebGL vendor spoofing ──
  const origGetParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function(param) {
    const UNMASKED_VENDOR = 0x9245;
    const UNMASKED_RENDERER = 0x9246;
    if (param === UNMASKED_VENDOR) return 'Intel Inc.';
    if (param === UNMASKED_RENDERER) return 'Intel Iris OpenGL Engine';
    return origGetParameter.apply(this, arguments);
  };

  // ── 6. Languages stack override ──
  Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en', 'ar'],
    configurable: true
  });

  // ── 7. Hardware concurrency (use real value, don't expose 4 as bot) ──
  // Already real in Chrome; added for safety
  Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => Math.max(4, navigator.hardwareConcurrency || 4),
    configurable: true
  });

  // ── 8. Plugin array (some sites check this) ──
  Object.defineProperty(navigator, 'plugins', {
    get: () => {
      if (navigator.plugins && navigator.plugins.length > 0) return navigator.plugins;
      // Return minimal fake array
      return [0,1,2].map(i => ({name: `Plugin ${i}`, length: 0}));
    },
    configurable: true
  });

  console.log('[JHPro] Stealth inject loaded at document_start');
})();
