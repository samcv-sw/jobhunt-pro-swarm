document.addEventListener('DOMContentLoaded', () => {
    const apiKeyInput = document.getElementById('apiKey');
    const professionInput = document.getElementById('profession');
    const baseCvInput = document.getElementById('baseCv');
    const saveBtn = document.getElementById('saveBtn');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const statusDiv = document.getElementById('status');

    // Load existing settings
    chrome.storage.local.get(['profession', 'baseCv', 'apiKey'], (result) => {
        if (result.profession) professionInput.value = result.profession;
        if (result.baseCv) baseCvInput.value = result.baseCv;
        if (result.apiKey) apiKeyInput.value = result.apiKey;
    });

    // Save settings
    saveBtn.addEventListener('click', () => {
        const profession = professionInput.value.trim();
        const baseCv = baseCvInput.value.trim();
        const apiKey = apiKeyInput.value.trim();

        chrome.storage.local.set({ profession, baseCv, apiKey }, () => {
            statusDiv.style.display = 'block';
            statusDiv.textContent = 'Settings Saved Successfully!';
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 2000);
        });
    });

    // Scrape Current Job
    scrapeBtn.addEventListener('click', () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const activeTab = tabs[0];
            scrapeBtn.textContent = 'Scraping...';
            chrome.tabs.sendMessage(activeTab.id, { action: "SCRAPE_JOB" }, (response) => {
                if(chrome.runtime.lastError) {
                    scrapeBtn.textContent = 'Error: Not a job page';
                    setTimeout(() => { scrapeBtn.textContent = '⚡ Scrape Current Job'; }, 2000);
                    return;
                }
                if (response && response.success) {
                    scrapeBtn.textContent = 'Job Sent to Backend!';
                    setTimeout(() => { scrapeBtn.textContent = '⚡ Scrape Current Job'; }, 2000);
                } else {
                    scrapeBtn.textContent = 'Error Scraping';
                    setTimeout(() => { scrapeBtn.textContent = '⚡ Scrape Current Job'; }, 2000);
                }
            });
        });
    });
});
