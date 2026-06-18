// Listen for background tasks
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "SEND_GMAIL") {
        sendEmail(request.payload.to, request.payload.subject, request.payload.body, request.taskId, sendResponse);
        return true; // Keep message channel open for async response
    }
});

function sendEmail(to, subject, body, taskId, sendResponse) {
    // Gmail uses a hash URL to open compose window: #inbox?compose=new
    if (!window.location.hash.includes('compose=new')) {
        window.location.hash = 'inbox?compose=new';
    }

    // Wait for the compose window to render
    let attempts = 0;
    const interval = setInterval(() => {
        attempts++;
        const toField = document.querySelector('input[peoplekit-id]'); // Gmail 'To' input
        const subjectField = document.querySelector('input[name="subjectbox"]');
        const bodyField = document.querySelector('div[aria-label="Message Body"]');
        const sendBtn = document.querySelector('div[data-tooltip^="Send"]');

        if (toField && subjectField && bodyField && sendBtn) {
            clearInterval(interval);
            
            const sleep = (ms) => new Promise(r => setTimeout(r, ms));
            
            (async () => {
                // Humanized pacing: wait before starting typing
                await sleep(Math.random() * 800 + 500);
                
                // Fill fields
                toField.value = to;
                toField.dispatchEvent(new Event('input', { bubbles: true }));
                toField.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' })); // Lock in the email address
                
                await sleep(Math.random() * 500 + 300);
                
                subjectField.value = subject;
                subjectField.dispatchEvent(new Event('input', { bubbles: true }));

                await sleep(Math.random() * 600 + 400);

                // Insert HTML into the contenteditable body
                bodyField.focus();
                document.execCommand('insertHTML', false, body);

                // Click send after a humanized delay of 1.5s - 3s
                await sleep(Math.random() * 1500 + 1500);
                sendBtn.click();
                sendResponse({ success: true });
            })();
        } else if (attempts > 10) {
            clearInterval(interval);
            console.error("JobHunt Pro: Failed to find Gmail compose elements.");
            sendResponse({ success: false, error: "UI elements not found" });
        }
    }, 500);
}
