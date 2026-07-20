const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'web', 'static', 'service-worker.js');
const content = fs.readFileSync(filePath, 'utf8');

const checks = [
  { string: 'OFFLINE_URL', description: 'OFFLINE_URL constant' },
  { string: 'jobhunt-pro-v3-dynamic', description: 'cache name jobhunt-pro-v3-dynamic' },
  { string: 'clients.claim', description: 'clients.claim() call' },
  { string: 'Promise.allSettled', description: 'Promise.allSettled usage' }
];

let allPassed = true;

for (const check of checks) {
  if (content.includes(check.string)) {
    console.log(`✓ ${check.description} found`);
  } else {
    console.log(`✗ ${check.description} NOT FOUND`);
    allPassed = false;
  }
}

if (allPassed) {
  console.log('\nAll checks passed. Service worker is correctly configured.');
  process.exit(0);
} else {
  console.log('\nSome checks failed. Please review the service worker.');
  process.exit(1);
}