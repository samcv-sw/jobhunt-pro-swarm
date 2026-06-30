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
        
        // Wait for the modal to appear
        console.log("Waiting for modal to load...");
        await new Promise(r => setTimeout(r, 2500));
        
        // Look for the Submit Application or Next button inside the modal
        const modalButtons = Array.from(document.querySelectorAll('button')).filter(btn => 
            btn.innerText.includes('Submit application') || 
            btn.innerText.includes('Next') ||
            btn.innerText.includes('التالي') ||
            btn.innerText.includes('إرسال الطلب')
        );

        if (modalButtons.length > 0) {
            console.log("🎯 Modal interactive button found! Proceeding with auto-fill/submit.");
            const actionBtn = modalButtons[0] as HTMLElement;
            await new Promise(r => setTimeout(r, Math.random() * 1000 + 500));
            actionBtn.click();
        } else {
            console.log("⚠️ Could not find Next/Submit button in modal. Form might require complex manual input.");
        }

        chrome.runtime.sendMessage({ action: "JOB_APPLIED", details: "Clicked Easy Apply button and interacted with modal." });
    } else {
        console.log("⚠️ No Easy Apply buttons found on this page.");
    }
}
