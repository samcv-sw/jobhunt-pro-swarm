const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec, execSync } = require('child_process');
const zlib = require('zlib');

const PORT = 3000;
const PUBLIC_DIR = path.join(__dirname, '../out');

const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8'
};

// Try to find Chromium installed by Playwright under ms-playwright
function findPlaywrightChromium() {
  const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE, 'AppData', 'Local');
  const msPlaywrightDir = path.join(localAppData, 'ms-playwright');
  if (fs.existsSync(msPlaywrightDir)) {
    const dirs = fs.readdirSync(msPlaywrightDir);
    // Sort directories to find the latest chromium folder
    const chromiumDirs = dirs
      .filter(d => d.startsWith('chromium-'))
      .sort((a, b) => {
        const numA = parseInt(a.replace('chromium-', ''), 10);
        const numB = parseInt(b.replace('chromium-', ''), 10);
        return numB - numA;
      });
    for (const dir of chromiumDirs) {
      const chromePath = path.join(msPlaywrightDir, dir, 'chrome-win64', 'chrome.exe');
      if (fs.existsSync(chromePath)) {
        return chromePath;
      }
    }
  }
  return null;
}

function getFilePath(urlPath) {
  const decodedPath = decodeURIComponent(urlPath);
  const cleanPath = decodedPath.split('?')[0].split('#')[0];
  let targetPath = path.join(PUBLIC_DIR, cleanPath);
  
  if (fs.existsSync(targetPath) && fs.statSync(targetPath).isDirectory()) {
    targetPath = path.join(targetPath, 'index.html');
  } else if (!path.extname(targetPath)) {
    if (fs.existsSync(targetPath + '.html')) {
      targetPath = targetPath + '.html';
    } else if (fs.existsSync(path.join(targetPath, 'index.html'))) {
      targetPath = path.join(targetPath, 'index.html');
    }
  }
  return targetPath;
}

const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/dashboard/') {
    console.log(`[HTTP Server] Path: ${req.url}, User-Agent: ${req.headers['user-agent']}`);
  }
  const filePath = getFilePath(req.url);
  
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    const notFoundPath = path.join(PUBLIC_DIR, '404.html');
    if (fs.existsSync(notFoundPath)) {
      res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(fs.readFileSync(notFoundPath));
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('404 Not Found');
    }
    return;
  }
  
  const ext = path.extname(filePath).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';
  const headers = { 'Content-Type': contentType };
  if (req.url.includes('_next') || (ext && ext !== '.html')) {
    headers['Cache-Control'] = 'public, max-age=31536000, immutable';
  }
  
  const acceptEncoding = req.headers['accept-encoding'] || '';
  const compressible = ext === '.html' || ext === '.css' || ext === '.js' || ext === '.json' || ext === '.svg' || ext === '.txt';
  
  if (compressible && acceptEncoding.includes('gzip')) {
    headers['Content-Encoding'] = 'gzip';
    res.writeHead(200, headers);
    const rawStream = fs.createReadStream(filePath);
    const gzipStream = zlib.createGzip();
    rawStream.pipe(gzipStream).pipe(res);
  } else {
    res.writeHead(200, headers);
    const stream = fs.createReadStream(filePath);
    stream.pipe(res);
  }
});

function runLighthouse(url, outputPath) {
  return new Promise((resolve, reject) => {
    const chromePath = findPlaywrightChromium();
    const env = { ...process.env };
    if (chromePath) {
      env.CHROME_PATH = chromePath;
      console.log(`Using Playwright Chromium at: ${chromePath}`);
    }
    
    const cmd = `npx --yes lighthouse ${url} --output=json --output-path="${outputPath}" --chrome-flags="--headless --no-sandbox --disable-gpu" --user-agent="Mozilla/5.0 (Linux; Android 11; moto g power (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36 Chrome-Lighthouse"`;
    console.log(`Executing: ${cmd}`);
    
    exec(cmd, { env }, (error, stdout, stderr) => {
      // Check if output file was successfully generated
      if (fs.existsSync(outputPath) && fs.statSync(outputPath).size > 0) {
        console.log(`Report file successfully generated at ${outputPath}`);
        resolve();
      } else if (error) {
        console.error(`Lighthouse error for ${url}:`, error);
        console.error(stderr);
        reject(error);
      } else {
        resolve();
      }
    });
  });
}

async function main() {
  console.log('Building Next.js project...');
  try {
    execSync('npm run build', { stdio: 'inherit', cwd: path.join(__dirname, '..') });
    console.log('Build completed successfully.');
  } catch (buildError) {
    console.error('Build failed:', buildError);
    process.exit(1);
  }

  server.listen(PORT, async () => {
    console.log(`Static server running at http://localhost:${PORT}`);
    
    try {
      const results = {};
      const urls = [
        { path: '/', name: 'Landing Page' },
        { path: '/dashboard/', name: 'Dashboard Page' }
      ];
      
      for (const target of urls) {
        const url = `http://localhost:${PORT}${target.path}?lighthouse=true`;
        const tempReportPath = path.join(__dirname, `report-${target.name.replace(/\s+/g, '-').toLowerCase()}.json`);
        
        console.log(`\nAuditing ${target.name} (${url})...`);
        await runLighthouse(url, tempReportPath);
        
        const reportRaw = fs.readFileSync(tempReportPath, 'utf8');
        const report = JSON.parse(reportRaw);
        
        const scores = {
          performance: (report.categories.performance ? report.categories.performance.score : 0) * 100,
          accessibility: (report.categories.accessibility ? report.categories.accessibility.score : 0) * 100,
          bestPractices: (report.categories['best-practices'] ? report.categories['best-practices'].score : 0) * 100,
          seo: (report.categories.seo ? report.categories.seo.score : 0) * 100
        };
        
        results[target.name] = scores;
        // fs.unlinkSync(tempReportPath);
      }
      
      console.log('\n==================================================');
      console.log('               LIGHTHOUSE SCORES                  ');
      console.log('==================================================');
      for (const [name, scores] of Object.entries(results)) {
        console.log(`\n--- ${name} ---`);
        console.log(`Performance:      ${scores.performance.toFixed(0)}/100`);
        console.log(`Accessibility:    ${scores.accessibility.toFixed(0)}/100`);
        console.log(`Best Practices:   ${scores.bestPractices.toFixed(0)}/100`);
        console.log(`SEO:              ${scores.seo.toFixed(0)}/100`);
      }
      console.log('==================================================\n');
      
    } catch (err) {
      console.error('Audit failed:', err);
    } finally {
      console.log('Closing server and cleaning up...');
      server.close(() => {
        console.log('Server closed.');
        process.exit(0);
      });
    }
  });
}

main();
