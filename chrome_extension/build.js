const fs = require('fs-extra');
const path = require('path');
const JavaScriptObfuscator = require('javascript-obfuscator');

const srcDir = __dirname;
const distDir = path.join(__dirname, 'dist');

async function build() {
    console.log('Starting JobHunt Pro Extension Build...');
    
    // Clean and recreate dist
    await fs.remove(distDir);
    await fs.ensureDir(distDir);

    // Files to process
    const jsFiles = ['background.js', 'scraper-content.js', 'chatgpt-content.js', 'gmail-content.js', 'popup.js'];
    const otherFiles = ['manifest.json', 'popup.html', 'content.css'];

    // Obfuscation options (aggressive to prevent tampering)
    const obfuscationOptions = {
        compact: true,
        controlFlowFlattening: true,
        controlFlowFlatteningThreshold: 1,
        deadCodeInjection: true,
        deadCodeInjectionThreshold: 0.4,
        debugProtection: true,
        debugProtectionInterval: 4000,
        disableConsoleOutput: true,
        identifierNamesGenerator: 'hexadecimal',
        log: false,
        numbersToExpressions: true,
        renameGlobals: false,
        selfDefending: true,
        simplify: true,
        splitStrings: true,
        splitStringsChunkLength: 5,
        stringArray: true,
        stringArrayCallsTransform: true,
        stringArrayCallsTransformThreshold: 1,
        stringArrayEncoding: ['rc4'],
        stringArrayIndexShift: true,
        stringArrayRotate: true,
        stringArrayShuffle: true,
        stringArrayWrappersCount: 5,
        stringArrayWrappersChainedCalls: true,
        stringArrayWrappersParametersMaxCount: 5,
        stringArrayWrappersType: 'function',
        stringArrayThreshold: 1,
        transformObjectKeys: true,
        unicodeEscapeSequence: false
    };

    // Copy other files
    for (const file of otherFiles) {
        if (await fs.pathExists(path.join(srcDir, file))) {
            await fs.copy(path.join(srcDir, file), path.join(distDir, file));
            console.log(`Copied ${file}`);
        }
    }

    // Obfuscate JS files
    for (const file of jsFiles) {
        if (await fs.pathExists(path.join(srcDir, file))) {
            const code = await fs.readFile(path.join(srcDir, file), 'utf8');
            console.log(`Obfuscating ${file}...`);
            const obfuscationResult = JavaScriptObfuscator.obfuscate(code, obfuscationOptions);
            await fs.writeFile(path.join(distDir, file), obfuscationResult.getObfuscatedCode());
            console.log(`Obfuscated and saved ${file}`);
        }
    }

    console.log('\n✅ Build complete! The secure extension is ready in the /dist folder.');
}

build().catch(console.error);
