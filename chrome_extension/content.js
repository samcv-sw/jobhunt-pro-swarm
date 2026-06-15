// content.js - Injected into LinkedIn / Indeed

function createAIApplyButton() {
    const btn = document.createElement("button");
    btn.innerHTML = "🚀 1-Click AI Apply via JobHunt Pro";
    btn.className = "jobhunt-pro-btn";
    btn.onclick = (e) => {
        e.preventDefault();
        extractAndApply();
    };
    return btn;
}

function injectButton() {
    // Check if we already injected
    if (document.querySelector(".jobhunt-pro-btn")) return;

    // LinkedIn Job View
    const liContainer = document.querySelector(".jobs-apply-button--top-card");
    if (liContainer) {
        liContainer.appendChild(createAIApplyButton());
    }

    // Indeed Job View
    const indeedContainer = document.querySelector("#applyButtonLinkContainer");
    if (indeedContainer) {
        indeedContainer.appendChild(createAIApplyButton());
    }
}

function extractAndApply() {
    let title = document.title;
    let description = document.body.innerText.substring(0, 5000); // Grab top 5000 chars

    // Send data to background script
    chrome.runtime.sendMessage({
        action: "apply_via_ai",
        data: {
            url: window.location.href,
            title: title,
            description: description
        }
    });

    // Provide immediate UI feedback
    const btn = document.querySelector(".jobhunt-pro-btn");
    btn.innerHTML = "✅ Sent to JobHunt Queue";
    btn.style.background = "#10b981";
    btn.disabled = true;
}

// Observe DOM changes (SPAs like LinkedIn don't reload the page)
const observer = new MutationObserver(() => {
    injectButton();
});

observer.observe(document.body, { childList: true, subtree: true });
