// Scrape LinkedIn Job details
function scrapeJob() {
    let title = document.querySelector('.job-details-jobs-unified-top-card__job-title')?.innerText || '';
    if (!title) {
        title = document.querySelector('h1')?.innerText || '';
    }

    let company = document.querySelector('.job-details-jobs-unified-top-card__company-name')?.innerText || '';
    if (!company) {
        company = document.querySelector('.jobs-unified-top-card__company-name')?.innerText || '';
    }

    let description = document.querySelector('#job-details')?.innerText || '';

    return { title, company, description };
}

// Inject Apply Button
function injectButton() {
    if (document.getElementById('jobhunt-auto-apply-btn')) return;

    const container = document.querySelector('.job-details-jobs-unified-top-card__content--two-pane');
    if (!container) return;

    const btn = document.createElement('button');
    btn.id = 'jobhunt-auto-apply-btn';
    btn.innerText = '🤖 Auto-Apply with JobHunt Pro';
    btn.style.cssText = `
        background-color: #0ea5e9;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        cursor: pointer;
        margin-left: 10px;
        font-family: inherit;
        font-size: 14px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        z-index: 9999;
    `;

    btn.addEventListener('click', async () => {
        btn.innerText = '⏳ Processing with AI...';
        btn.disabled = true;
        
        const jobData = scrapeJob();
        if (!jobData.description) {
            alert('Could not scrape job description.');
            btn.innerText = '🤖 Auto-Apply with JobHunt Pro';
            btn.disabled = false;
            return;
        }

        // Send message to background script to initiate ChatGPT flow
        chrome.runtime.sendMessage({
            action: "START_AI_GENERATION",
            job: jobData
        }, (response) => {
            if (response && response.status === 'success') {
                btn.innerText = '✅ Cover Letter Ready!';
                btn.style.backgroundColor = '#10b981';
                
                // Show the result in an alert for now, or copy to clipboard
                console.log("Generated Cover Letter:\n", response.text);
                navigator.clipboard.writeText(response.text);
                alert("Cover letter copied to clipboard!");
            } else {
                btn.innerText = '❌ Failed';
                btn.style.backgroundColor = '#ef4444';
                alert("Error: " + (response?.error || 'Unknown error'));
            }
            setTimeout(() => {
                btn.innerText = '🤖 Auto-Apply with JobHunt Pro';
                btn.disabled = false;
                btn.style.backgroundColor = '#0ea5e9';
            }, 5000);
        });
    });

    const actionContainer = container.querySelector('.mt5');
    if (actionContainer) {
        actionContainer.appendChild(btn);
    } else {
        container.appendChild(btn);
    }
}

// Observe DOM for changes (LinkedIn is a SPA)
const observer = new MutationObserver(() => {
    injectButton();
});
observer.observe(document.body, { childList: true, subtree: true });

// Initial inject
setTimeout(injectButton, 2000);

// Listen for background tasks (Piggybacking)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "DO_SCRAPE") {
        // Scrape list of jobs from the search page
        const jobCards = document.querySelectorAll('.job-card-container');
        const jobs = [];
        
        jobCards.forEach(card => {
            const title = card.querySelector('.job-card-list__title')?.innerText?.trim();
            const company = card.querySelector('.job-card-container__primary-description')?.innerText?.trim();
            const location = card.querySelector('.job-card-container__metadata-item')?.innerText?.trim();
            
            if (title && company) {
                jobs.push({ title, company, location });
            }
        });
        
        sendResponse({ status: "success", jobs: jobs });
    }
    return true;
});
