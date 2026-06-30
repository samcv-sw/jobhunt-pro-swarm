console.log("JobHunt Pro Swarm Injected.");

// Listen for messages from the Popup/Background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "START_SWARM") {
        console.log("🚀 Swarm Protocol Initiated!");
        startLinkedInHack();
        sendResponse({ status: "running" });
    }
});

async function startLinkedInHack() {
    console.log("Scanning DOM for Easy Apply buttons...");
    
    // Attempt to find the Easy Apply button on LinkedIn
    const applyButtons = Array.from(document.querySelectorAll('button')).filter(btn => 
        btn.innerText.includes('Easy Apply') || 
        btn.innerText.includes('Apply now') ||
        btn.innerText.includes('تقديم سهل')
    );

    if (applyButtons.length > 0) {
        console.log(`🎯 Found ${applyButtons.length} potential Easy Apply buttons!`);
        const targetBtn = applyButtons[0] as HTMLElement;
        
        // Simulating human mouse movement delay
        await new Promise(r => setTimeout(r, Math.random() * 2000 + 1000));
        
        console.log("Clicking Easy Apply...");
        targetBtn.click();
        
        // TODO: In a full version, we parse the popup modal and fill fields via DOM injection.
        // For now, notify the background script that we clicked it.
        chrome.runtime.sendMessage({ action: "JOB_APPLIED", details: "Clicked Easy Apply button." });
    } else {
        console.log("⚠️ No Easy Apply buttons found on this page.");
    }
}
