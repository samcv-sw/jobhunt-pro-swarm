import worker from '../../frontend/public/_worker.js';
import assert from 'assert';

// We will mock the global fetch function.
let lastFetchTarget = null;
let lastFetchInit = null;

globalThis.fetch = async (target, init) => {
  lastFetchTarget = target;
  lastFetchInit = init;
  return new Response('mocked_backend_response', {
    status: 200,
    headers: new Headers({ 'x-mock-backend': 'true' })
  });
};

async function runTests() {
  console.log('Running worker proxy tests...');

  // Test Case 1: Proxy GET to /api/jobs
  {
    lastFetchTarget = null;
    lastFetchInit = null;
    const req = new Request('https://my-pages-site.pages.dev/api/jobs?limit=10', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer test-token',
        'Custom-Header': 'custom-value'
      }
    });
    const env = {
      ASSETS: {
        fetch: async () => new Response('should not be called')
      }
    };
    const res = await worker.fetch(req, env, {});
    const text = await res.text();

    assert.strictEqual(text, 'mocked_backend_response');
    assert.strictEqual(lastFetchTarget, 'https://jhfguf.pythonanywhere.com/api/jobs?limit=10');
    assert.strictEqual(lastFetchInit.method, 'GET');
    assert.strictEqual(lastFetchInit.headers.get('Host'), 'jhfguf.pythonanywhere.com');
    assert.strictEqual(lastFetchInit.headers.get('Authorization'), 'Bearer test-token');
    assert.strictEqual(lastFetchInit.headers.get('Custom-Header'), 'custom-value');
    console.log('✓ Test Case 1: GET proxy to /api/ passed');
  }

  // Test Case 2: Proxy POST with body to /scrape
  {
    lastFetchTarget = null;
    lastFetchInit = null;
    const req = new Request('https://my-pages-site.pages.dev/scrape', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url: 'https://example.com' })
    });
    const env = {
      ASSETS: {
        fetch: async () => new Response('should not be called')
      }
    };
    const res = await worker.fetch(req, env, {});
    
    assert.strictEqual(lastFetchTarget, 'https://jhfguf.pythonanywhere.com/scrape');
    assert.strictEqual(lastFetchInit.method, 'POST');
    assert.strictEqual(lastFetchInit.headers.get('Host'), 'jhfguf.pythonanywhere.com');
    assert.ok(lastFetchInit.body !== null);
    console.log('✓ Test Case 2: POST proxy to /scrape passed');
  }

  // Test Case 3: WebSocket Upgrade /ws/
  {
    lastFetchTarget = null;
    lastFetchInit = null;
    const req = new Request('https://my-pages-site.pages.dev/ws/connect', {
      headers: {
        'Upgrade': 'websocket'
      }
    });
    const env = {
      ASSETS: {
        fetch: async () => new Response('should not be called')
      }
    };
    await worker.fetch(req, env, {});
    
    assert.strictEqual(lastFetchTarget, 'wss://jhfguf.pythonanywhere.com/ws/connect');
    console.log('✓ Test Case 3: WebSocket upgrade proxy passed');
  }

  // Test Case 4: Static assets fallback
  {
    let assetsCalled = false;
    const req = new Request('https://my-pages-site.pages.dev/dashboard/index.html');
    const env = {
      ASSETS: {
        fetch: async (r) => {
          assetsCalled = true;
          assert.strictEqual(r.url, 'https://my-pages-site.pages.dev/dashboard/index.html');
          return new Response('static_content');
        }
      }
    };
    const res = await worker.fetch(req, env, {});
    const text = await res.text();
    
    assert.strictEqual(text, 'static_content');
    assert.strictEqual(assetsCalled, true);
    console.log('✓ Test Case 4: Static assets fallback passed');
  }

  // Test Case 5: Error handling 502
  {
    globalThis.fetch = async () => {
      throw new Error('Network error');
    };
    const req = new Request('https://my-pages-site.pages.dev/api/jobs');
    const env = {};
    const res = await worker.fetch(req, env, {});
    assert.strictEqual(res.status, 502);
    const json = await res.json();
    assert.strictEqual(json.error, 'Backend unreachable via Cloudflare Pages Function Proxy');
    assert.strictEqual(json.detail, 'Network error');
    console.log('✓ Test Case 5: Error handling 502 passed');
  }

  console.log('All worker tests passed successfully!');
}

runTests().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
