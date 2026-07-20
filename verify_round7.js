const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const arLanding = path.join(ROOT, 'web/templates/index_v4.html');
const enLanding = path.join(ROOT, 'web/templates/en/index_v4.html');
const publicPy = path.join(ROOT, 'web/routers/public.py');

let pass = 0, fail = 0;
function check(name, cond) {
  if (cond) { console.log('  [PASS] ' + name); pass++; }
  else { console.log('  [FAIL] ' + name); fail++; }
}

// 1. Sitemap URL count
const py = fs.readFileSync(publicPy, 'utf8');
const sitemapBlock = py.slice(py.indexOf('<urlset'), py.indexOf('</urlset>') + 9);
const locs = (sitemapBlock.match(/<loc>/g) || []).length;
check('sitemap.xml contains >= 30 <loc> entries (got ' + locs + ')', locs >= 30);
const expected = [
  '/', '/pricing', '/referral', '/faq', '/blog', '/privacy', '/trust', '/compare',
  '/chrome-extension', '/terms', '/contact', '/services', '/roast', '/employers', '/employer/track',
  '/en/', '/en/pricing', '/en/faq', '/en/blog', '/en/compare', '/en/trust', '/en/chrome-extension',
  '/en/contact', '/en/privacy', '/en/terms', '/en/referral', '/en/track', '/en/services', '/en/roast', '/en/for-employers'
];
let missing = expected.filter(u => !sitemapBlock.includes('<loc>https://jhfguf.pythonanywhere.com' + u + '</loc>'));
check('sitemap.xml has all expected routes (missing: ' + (missing.length ? missing.join(',') : 'none') + ')', missing.length === 0);

// 2. hreflang on AR landing
const ar = fs.readFileSync(arLanding, 'utf8');
check('AR landing has hreflang=ar', /hreflang="ar"/.test(ar));
check('AR landing has hreflang=en', /hreflang="en"/.test(ar));
check('AR landing has hreflang=x-default', /hreflang="x-default"/.test(ar));

// 3. hreflang on EN landing
const en = fs.readFileSync(enLanding, 'utf8');
check('EN landing has hreflang=ar', /hreflang="ar"/.test(en));
check('EN landing has hreflang=en', /hreflang="en"/.test(en));
check('EN landing has hreflang=x-default', /hreflang="x-default"/.test(en));

console.log('\n' + (fail === 0 ? '🏆 ROUND 7 CHECKS PASSED (' + pass + '/' + (pass + fail) + ')' : '❌ ' + fail + ' FAILURES'));
process.exit(fail === 0 ? 0 : 1);
