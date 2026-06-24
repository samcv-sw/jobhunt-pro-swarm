// shadow-content.js
// This script perfectly extracts job data from LinkedIn and pushes it to our API.

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "SCRAPE_JOB") {
        console.log("Shadow Scraper: Extracting job data...");

        let title = document.querySelector('.job-details-jobs-unified-top-card__job-title')?.innerText.trim() || 'Unknown Title';
        let company = document.querySelector('.job-details-jobs-unified-top-card__company-name')?.innerText.trim() || 'Unknown Company';
        let description = document.querySelector('#job-details')?.innerText.trim() || '';

        // If not found in primary selectors, try alternative LinkedIn selectors
        if (title === 'Unknown Title') {
            title = document.querySelector('h1.top-card-layout__title')?.innerText.trim() || title;
            company = document.querySelector('a.topcard__org-name-link')?.innerText.trim() || company;
            description = document.querySelector('.description__text')?.innerText.trim() || description;
        }

        if (!description) {
            console.error("Shadow Scraper: Could not find job description.");
            sendResponse({ success: false, error: "No description found" });
            return true;
        }

        const jobUrl = window.location.href.split('?')[0];

        const jobData = {
            title: title,
            company: company,
            description: description,
            link: jobUrl,
            source: 'linkedin'
        };

        // Get API Key and Backend URL from storage
        chrome.storage.local.get(['apiKey'], async (result) => {
            const apiKey = result.apiKey || '';
            const backendUrl = "https://jhfguf.pythonanywhere.com"; // Hardcoded to the user's PythonAnywhere instance
            
            try {
                const response = await fetch(`${backendUrl}/api/extension/ingest`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${apiKey}`
                    },
                    body: JSON.stringify(jobData)
                });

                if (response.ok) {
                    console.log("Shadow Scraper: Successfully pushed to backend.");
                    sendResponse({ success: true });
                } else {
                    console.error("Shadow Scraper: Failed to push to backend.", response.statusText);
                    sendResponse({ success: false });
                }
            } catch (err) {
                console.error("Shadow Scraper: Fetch error.", err);
                sendResponse({ success: false });
            }
        });

        // Return true to indicate we wish to send a response asynchronously
        return true; 
    }
});
