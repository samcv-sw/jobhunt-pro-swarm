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

// Bezier curve math for human-like mouse movement
function cubicBezier(t: number, p0: number, p1: number, p2: number, p3: number): number {
    const u = 1 - t;
    const tt = t * t;
    const uu = u * u;
    const uuu = uu * u;
    const ttt = tt * t;
    return uuu * p0 + 3 * uu * t * p1 + 3 * u * tt * p2 + ttt * p3;
}

// Send CDP command to background script
function sendCDP(type: string, params: any): Promise<any> {
    return new Promise((resolve) => {
        chrome.runtime.sendMessage({ action: "CDP_DISPATCH", type, params }, (response) => {
            resolve(response);
        });
    });
}

// Advanced CDP-based Javascript Event Synthesizer
async function triggerNativeClick(element: HTMLElement) {
    const rect = element.getBoundingClientRect();
    const targetX = Math.round(rect.left + (rect.width / 2) + (Math.random() * 10 - 5));
    const targetY = Math.round(rect.top + (rect.height / 2) + (Math.random() * 10 - 5));
    
    console.log(`📡 Simulating CDP Pointer Clicks at [${targetX}, ${targetY}]...`);
    
    // 1. Simulate bezier mouse movement from (0,0) or current pos
    const startX = Math.random() * window.innerWidth;
    const startY = Math.random() * window.innerHeight;
    
    // Control points for curve
    const cp1X = startX + (targetX - startX) * Math.random();
    const cp1Y = startY + (targetY - startY) * Math.random();
    const cp2X = targetX + (startX - targetX) * Math.random();
    const cp2Y = targetY + (startY - targetY) * Math.random();
    
    const steps = Math.floor(Math.random() * 10) + 10; // 10 to 20 steps
    for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const x = cubicBezier(t, startX, cp1X, cp2X, targetX);
        const y = cubicBezier(t, startY, cp1Y, cp2Y, targetY);
        
        await sendCDP("Input.dispatchMouseEvent", {
            type: "mouseMoved",
            x: x,
            y: y
        });
        await new Promise(r => setTimeout(r, Math.random() * 10 + 5));
    }
    
    // 2. Add physiological tremor (jitter) over the target
    await sendCDP("Input.dispatchMouseEvent", {
        type: "mouseMoved",
        x: targetX + (Math.random() * 2 - 1),
        y: targetY + (Math.random() * 2 - 1)
    });
    
    await new Promise(r => setTimeout(r, Math.random() * 200 + 50));
    
    // 3. Dispatch CDP mouse pressed and released
    await sendCDP("Input.dispatchMouseEvent", {
        type: "mousePressed",
        x: targetX,
        y: targetY,
        button: "left",
        clickCount: 1
    });
    
    await new Promise(r => setTimeout(r, Math.random() * 80 + 20));
    
    await sendCDP("Input.dispatchMouseEvent", {
        type: "mouseReleased",
        x: targetX,
        y: targetY,
        button: "left",
        clickCount: 1
    });
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
