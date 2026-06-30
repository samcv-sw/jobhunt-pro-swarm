console.log("JobHunt Pro Swarm Injected.");

// Listen for messages from the Popup/Background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "START_SWARM") {
        console.log("🚀 Swarm Protocol Initiated!");
        startUniversalHack();
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

// Advanced Javascript Event Synthesizer (No Debugger UX warning)
async function triggerNativeClick(element: HTMLElement) {
    const rect = element.getBoundingClientRect();
    const x = Math.round(rect.left + (rect.width / 2) + (Math.random() * 10 - 5));
    const y = Math.round(rect.top + (rect.height / 2) + (Math.random() * 10 - 5));
    
    console.log(`📡 Simulating Advanced Pointer Clicks at [${x}, ${y}]...`);
    
    // Simulate complex user interaction
    const events = [
        new PointerEvent('pointerover', { bubbles: true, cancelable: true, clientX: x, clientY: y }),
        new PointerEvent('pointerenter', { bubbles: true, cancelable: true, clientX: x, clientY: y }),
        new MouseEvent('mouseover', { bubbles: true, cancelable: true, clientX: x, clientY: y }),
        new MouseEvent('mouseenter', { bubbles: true, cancelable: true, clientX: x, clientY: y })
    ];
    
    events.forEach(ev => element.dispatchEvent(ev));
    await new Promise(r => setTimeout(r, Math.random() * 200 + 50));
    
    element.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
    element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
    
    await new Promise(r => setTimeout(r, Math.random() * 80 + 20));
    
    element.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
    element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
    element.click(); // Final fallback trigger
}

// Swarm Core Logic - Universal ATS Engine
async function startUniversalHack() {
    console.log("🕵️‍♂️ Swarm Ghost Protocol: Initializing Universal ATS Scanner...");
    
    // 1. Scan and Fill Form Fields
    await scanAndFillFields();

    // 2. Observe the DOM for "Apply/Next/Submit" Buttons
    const observer = new MutationObserver(async (mutations, obs) => {
        const actionKeywords = ['apply', 'next', 'submit', 'continue', 'إرسال', 'التالي', 'تقديم'];
        const actionButtons = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"], a.btn')).filter(btn => {
            const text = (btn.innerText || (btn as HTMLInputElement).value || '').toLowerCase();
            return actionKeywords.some(keyword => text.includes(keyword));
        });

        if (actionButtons.length > 0) {
            obs.disconnect(); // Stop observing once we find our target
            console.log(`🎯 Target Locked: Found ${actionButtons.length} potential Action buttons!`);
            const targetBtn = actionButtons[0] as HTMLElement;
            
            await humanJitterDelay(1500, 3500);
            console.log("🖱️ Executing OS-Level Trusted Click on Action Button...");
            triggerNativeClick(targetBtn);
            
            // Re-init observer for subsequent modals or pages
            setTimeout(startUniversalHack, 3000); 
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    
    // Fallback trigger
    setTimeout(() => {
        document.body.setAttribute('data-swarm-ping', Date.now().toString());
    }, 1000);
}

// Simulated Local AI / Fuzzy Matcher for Form Fields
async function scanAndFillFields() {
    console.log("🔍 Scanning for Input Fields...");
    const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select');
    
    // Dummy user data (This would typically come from IndexedDB or Background Script)
    const userData: Record<string, string> = {
        'first name': 'Sam',
        'last name': 'Engineer',
        'email': 'sam@example.com',
        'phone': '+1234567890',
        'linkedin': 'https://linkedin.com/in/sam',
        'github': 'https://github.com/sam',
        'expected salary': '120000',
        'location': 'Remote'
    };

    for (const el of Array.from(inputs)) {
        const input = el as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
        
        // Skip already filled inputs
        if (input.value && input.value.trim() !== '') continue;

        // Try to identify the field context via id, name, placeholder, or preceding label
        let context = `${input.id} ${input.name} ${input.placeholder || ''}`.toLowerCase();
        
        // Find nearest label
        let label = document.querySelector(`label[for="${input.id}"]`);
        if (label) context += ` ${label.textContent?.toLowerCase()}`;
        else if (input.parentElement && input.parentElement.tagName.toLowerCase() === 'label') {
            context += ` ${input.parentElement.textContent?.toLowerCase()}`;
        }

        // Fuzzy match logic
        for (const [key, value] of Object.entries(userData)) {
            if (context.includes(key.split(' ')[0])) {
                console.log(`✍️ Filling matched field [${key}] -> ${value}`);
                input.value = value;
                
                // Dispatch events to trigger framework (React/Angular) state updates
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                await humanJitterDelay(300, 800); // Wait between fields to look human
                break;
            }
        }
    }
}
