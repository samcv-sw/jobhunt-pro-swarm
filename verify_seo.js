const fs = require('fs');

const files = [
  { path: 'web/templates/index_v4.html', name: 'Arabic RTL Landing (index_v4.html)', locale: 'ar' },
  { path: 'web/templates/en/roast.html', name: 'Roast Route (en/roast.html)', locale: 'en' },
  { path: 'web/templates/en/for_employers.html', name: 'For Employers (en/for_employers.html)', locale: 'en' }
];

const checks = [
  { key: 'og:title', re: /property=["']og:title["']/i },
  { key: 'og:type', re: /property=["']og:type["']/i },
  { key: 'og:description', re: /property=["']og:description["']/i },
  { key: 'og:url', re: /property=["']og:url["']/i },
  { key: 'og:image', re: /property=["']og:image["']/i },
  { key: 'twitter:card', re: /name=["']twitter:card["']/i },
  { key: 'twitter:title', re: /name=["']twitter:title["']/i },
  { key: 'twitter:description', re: /name=["']twitter:description["']/i },
  { key: 'twitter:image', re: /name=["']twitter:image["']/i },
  { key: 'description', re: /name=["']description["']/i },
  { key: 'title', re: /<title>/i },
  { key: 'canonical', re: /rel=["']canonical["']/i },
  { key: 'json-ld', re: /application\/ld\+json/i }
];

let allPass = true;
for (const f of files) {
  let html = '';
  try {
    html = fs.readFileSync(f.path, 'utf8');
  } catch (e) {
    console.log(`❌ ${f.name}: FILE NOT FOUND (${f.path})`);
    allPass = false;
    continue;
  }
  console.log(`\n=== ${f.name} ===`);
  for (const c of checks) {
    const ok = c.re.test(html);
    if (!ok) allPass = false;
    console.log(`  ${ok ? '✅' : '❌'} ${c.key}`);
  }
  // Check absolute URLs in og:image / twitter:image
  const absImg = /<meta\b[^>]*(?=[^>]*property=["']og:image["'])(?=[^>]*content=["']https:\/\/jhfguf\.pythonanywhere\.com)/i.test(html);
  const absUrl = /<meta\b[^>]*(?=[^>]*property=["']og:url["'])(?=[^>]*content=["']https:\/\/jhfguf\.pythonanywhere\.com)/i.test(html);
  console.log(`  ${absImg ? '✅' : '❌'} og:image absolute URL`);
  console.log(`  ${absUrl ? '✅' : '❌'} og:url absolute URL`);
  if (!absImg || !absUrl) allPass = false;
}

console.log(`\n${allPass ? '🏆 ALL SEO CHECKS PASSED' : '⚠️ SOME CHECKS FAILED'}`);
