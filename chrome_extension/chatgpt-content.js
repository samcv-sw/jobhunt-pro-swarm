let isGenerating = false;

function injectPromptAndSubmit(promptText, taskId, tabId) {
    if (isGenerating) return;
    isGenerating = true;

    // ChatGPT uses a contenteditable div or textarea with id #prompt-textarea
    const textarea = document.querySelector('#prompt-textarea');
    if (!textarea) {
        console.error("JobHunt Pro: Could not find ChatGPT prompt textarea.");
        isGenerating = false;
        return;
    }

    // Set value and trigger React's synthetic events
    textarea.focus();
    if (textarea.tagName === 'TEXTAREA') {
        textarea.value = promptText;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
    } else {
        textarea.innerText = promptText;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Find and click the submit button
    setTimeout(() => {
        const submitBtn = document.querySelector('button[data-testid="send-button"]');
        if (submitBtn) {
            submitBtn.click();
            monitorGeneration(taskId, tabId);
        } else {
            console.error("JobHunt Pro: Could not find ChatGPT submit button.");
            isGenerating = false;
        }
    }, 500);
}

function monitorGeneration(taskId, tabId) {
    let checkInterval = setInterval(() => {
        // The Stop button appears while generating
        const stopBtn = document.querySelector('button[aria-label="Stop generating"]');
        
        // If the stop button is gone, generation is likely complete
        if (!stopBtn) {
            // Give it 2 more seconds for the DOM to settle
            setTimeout(() => {
                extractResult(taskId, tabId);
            }, 2000);
            clearInterval(checkInterval);
        }
    }, 1000);
}

function extractResult(taskId, tabId) {
    // Get all markdown response blocks
    const responses = document.querySelectorAll('.markdown');
    if (responses.length > 0) {
        // The last one is the latest response
        const latestResponse = responses[responses.length - 1].innerText;
        
        chrome.runtime.sendMessage({
            action: "AI_GENERATION_COMPLETE",
            taskId: taskId,
            tabId: tabId,
            text: latestResponse
        });
    }
    isGenerating = false;
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "INJECT_PROMPT") {
        injectPromptAndSubmit(request.prompt, request.taskId, request.tabId);
    }
});

// Check if there's a pending prompt from a newly opened tab
chrome.storage.local.get(['pendingPrompt'], (storage) => {
    if (storage.pendingPrompt) {
        const promptData = storage.pendingPrompt;
        chrome.storage.local.remove('pendingPrompt');
        setTimeout(() => {
            injectPromptAndSubmit(promptData.prompt, promptData.taskId, promptData.tabId);
        }, 1500); // Wait for the page to fully hydrate
    }
});
