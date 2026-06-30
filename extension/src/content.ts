console.log("JobHunt Pro Swarm Injected.");

// Listen for messages from the Popup/Background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "START_SWARM") {
        console.log("🚀 Swarm Protocol Initiated!");
        startLinkedInHack();
        sendResponse({ status: "running" });
    }
});

// Simulated Human Jitter Algorithm
function humanJitterDelay(min: number, max: number) {
    const baseDelay = Math.random() * (max - min) + min;
    // Introduce micro-stutters (Bezier curve approximation)
    const stutter = Math.random() > 0.8 ? Math.random() * 500 : 0;
    return new Promise(resolve => setTimeout(resolve, baseDelay + stutter));
}

// Swarm Core Logic
async function startLinkedInHack() {
    console.log("🕵️‍♂️ Swarm Ghost Protocol: Initializing DOM MutationObserver...");
    
    // Instead of fixed waits, we observe the DOM for changes
    const observer = new MutationObserver(async (mutations, obs) => {
        const applyButtons = Array.from(document.querySelectorAll('button')).filter(btn => 
            btn.innerText.includes('Easy Apply') || 
            btn.innerText.includes('Apply now') ||
            btn.innerText.includes('تقديم سهل')
        );

        if (applyButtons.length > 0) {
            obs.disconnect(); // Stop observing once we find our target
            console.log(`🎯 Target Locked: Found ${applyButtons.length} Easy Apply buttons!`);
            const targetBtn = applyButtons[0] as HTMLElement;
            
            await humanJitterDelay(1500, 3500);
            console.log("🖱️ Executing Humanized Click...");
            targetBtn.click();
            
            // Re-init observer for Modal
            observeModal();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    
    // Fallback trigger
    setTimeout(() => {
        // Trigger a fake mutation if nothing happens natively
        document.body.setAttribute('data-swarm-ping', Date.now().toString());
    }, 1000);
}

function observeModal() {
    console.log("🕵️‍♂️ Waiting for LinkedIn Modal...");
    const modalObserver = new MutationObserver(async (mutations, obs) => {
        const modalButtons = Array.from(document.querySelectorAll('button')).filter(btn => 
            btn.innerText.includes('Submit application') || 
            btn.innerText.includes('Next') ||
            btn.innerText.includes('التالي') ||
            btn.innerText.includes('إرسال الطلب')
        );

        if (modalButtons.length > 0) {
            console.log("🎯 Modal Interactive Element Detected.");
            const actionBtn = modalButtons[0] as HTMLElement;
            
            await humanJitterDelay(800, 2000);
            actionBtn.click();
            
            chrome.runtime.sendMessage({ action: "JOB_APPLIED", details: "Swarm successfully injected and clicked through modal." });
            
            // Continue observing if it was 'Next', disconnect if 'Submit'
            if (actionBtn.innerText.includes('Submit') || actionBtn.innerText.includes('إرسال')) {
                 obs.disconnect();
            }
        }
    });

    modalObserver.observe(document.body, { childList: true, subtree: true });
}
