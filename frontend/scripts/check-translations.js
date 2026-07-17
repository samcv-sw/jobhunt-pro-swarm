const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('--- Starting Translation Verification Script ---');

const projectRoot = path.resolve(__dirname, '..', '..');
const pagePath = path.resolve(projectRoot, 'frontend', 'src', 'app', 'page.tsx');
const dashboardPath = path.resolve(projectRoot, 'frontend', 'src', 'app', 'dashboard', 'page.tsx');

let errors = 0;

function checkFile(filePath) {
  console.log(`Scanning file: ${filePath}`);
  const content = fs.readFileSync(filePath, 'utf8');

  // Rule 1: No inline translation ternaries like `isArabic ? "Arabic" : "English"`
  // Ignore layout directives like "rtl" vs "ltr" and arrow directions
  const ternaryRegex = /isArabic\s*\?\s*["'`]([^"'`]+)["'`]\s*:\s*["'`]([^"'`]+)["'`]/g;
  let match;
  while ((match = ternaryRegex.exec(content)) !== null) {
    const val1 = match[1];
    const val2 = match[2];
    if ((val1 === 'rtl' && val2 === 'ltr') || (val1 === 'ltr' && val2 === 'rtl')) continue;
    if ((val1 === '→' && val2 === '←') || (val1 === '←' && val2 === '→')) continue;
    
    console.error(`Error: Found inline translation ternary in ${path.basename(filePath)}: "${match[0]}"`);
    errors++;
  }

  // Rule 2: No hardcoded English UI strings from our predefined lists
  const forbiddenEnglishStrings = [
    "Decentralized Control Hub",
    "Hydra 1M-User Zero-Cost System Infrastructure",
    "Max Capacity: 1,000,000 Concurrent Users",
    "Active at Cloud Edge",
    "Turso Database Sharding Simulator",
    "Calculate FNV-1a consistent hashing to resolve target database shard index.",
    "Tenant Name / ID:",
    "Resolve Shard",
    "FNV-1a Hash:",
    "Assigned Shard Server:",
    "Connection URL:",
    "Browser SQLite (Wasm-OPFS)",
    "Manage local persistent WebAssembly SQLite instance running in the browser.",
    "Engine Status:",
    "Pending Mutations to Sync:",
    "Sync Now",
    "Wipe Local DB",
    "Outbound Delivery Settings (BYO SMTP)",
    "Send application emails directly from your address. Encrypted end-to-end, zero SaaS cost.",
    "Sender Email Address:",
    "App Token / Password:",
    "Test & Save Connection",
    "Note: Passwords are encrypted on-device before storage using AES-256 standard.",
    "e.g. Demo User",
    "System Status Overview",
    "Total Sharded DB Instances",
    "Edge Redis Task Queue",
    "Online (Upstash REST)",
    "Outbound SMTP Fallback Pool",
    "Active (1,500/day free limit)",
    "Edge Response Latency",
    "Visual Representation of 500 Shards",
    "Active Users",
    "Active Campaigns",
    "Sent Applications",
    "Status: Operational",
    "Latency: 14ms",
    "Server Cost: $0.00/mo",
    "AI Automation Dashboard",
    "Monitor & manage application campaigns and smart job extraction",
    "Back to Home",
    "Live Statistics",
    "Total Scrapes",
    "Success Rate",
    "Active Scrapers",
    "System Load",
    "Running",
    "Idle",
    "Healthy",
    "Optimal",
    "Historical Scrapes & Applications",
    "Detailed list of recent scraped jobs and their application status",
    "Search company, job title or source...",
    "Date & Time",
    "Company",
    "Job Title",
    "Source",
    "Status",
    "Actions",
    "Completed",
    "Processing",
    "Failed",
    "Retry",
    "View Details",
    "Weekly Performance Analytics",
    "Weekly job scraping volume vs acceptance rate comparison",
    "Scraped Jobs",
    "Submitted Apps",
    "Infrastructure is fully deployed at Cloud Edge with zero operational overhead.",
    "SQLite WASM OPFS Storage",
    "Showing {filtered} of {total} entries",
    "AI Recommendation",
    "Application success is optimal at 94%. We suggest scaling LinkedIn scraping volume in the next 12 hours based on profile matches."
  ];

  forbiddenEnglishStrings.forEach(str => {
    const escaped = str.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    
    // Pattern 1: as JSX text node: >Forbidden String<
    const jsxTextRegex = new RegExp(`>\\s*${escaped}\\s*<`);
    // Pattern 2: as JSX curly brace text: {"Forbidden String"}
    const jsxCurlyRegex = new RegExp(`{\\s*["'\`]${escaped}["'\`]\\s*}`);
    // Pattern 3: as an attribute value: label="Forbidden String" or placeholder="Forbidden String"
    const jsxAttrRegex = new RegExp(`=\\s*["'\`]${escaped}["'\`]`);
    // Pattern 4: in a ternary return: ? "Forbidden String" :
    const ternaryValRegex = new RegExp(`[?:]\\s*["'\`]${escaped}["'\`]`);

    if (jsxTextRegex.test(content) || jsxCurlyRegex.test(content) || jsxAttrRegex.test(content) || ternaryValRegex.test(content)) {
      console.error(`Error: Found hardcoded English UI string/attribute: "${str}"`);
      errors++;
    }
  });

  // Rule 3: Check for JSX text nodes containing English alphabet characters directly (excluding tags/imports)
  const rawJsxTextRegex = />\s*[A-Za-z][A-Za-z\s:,.!?-]+\s*</g;
  const rawTexts = content.match(rawJsxTextRegex);
  if (rawTexts) {
    const actualRawTexts = rawTexts.filter(t => {
      const clean = t.replace(/[><]/g, '').trim();
      return clean.length > 2 && clean !== 'H' && clean !== '✓' && clean !== '✗';
    });
    if (actualRawTexts.length > 0) {
      console.error(`Error: Found potential raw JSX text in ${path.basename(filePath)}:`);
      actualRawTexts.forEach(t => console.error(`  - ${t}`));
      errors++;
    }
  }
}

try {
  checkFile(pagePath);
  checkFile(dashboardPath);
} catch (e) {
  console.error('Failed to parse pages:', e.message);
  process.exit(1);
}

if (errors > 0) {
  console.error(`Verification FAILED with ${errors} translation error(s).`);
  process.exit(1);
} else {
  console.log('✓ All pages verified. Zero hardcoded English strings or inline translation ternaries found.');
}

console.log('Running backend pytest suite to verify zero regressions...');
try {
  execSync('test_env\\Scripts\\pytest', {
    cwd: projectRoot,
    stdio: 'inherit'
  });
  console.log('✓ Pytest suite completed successfully!');
} catch (error) {
  console.error('Error: Pytest suite failed!');
  process.exit(1);
}

console.log('--- Translation Verification Successful! ---');
