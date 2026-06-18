document.addEventListener('DOMContentLoaded', () => {
    const professionInput = document.getElementById('profession');
    const baseCvInput = document.getElementById('baseCv');
    const saveBtn = document.getElementById('saveBtn');
    const statusDiv = document.getElementById('status');

    // Load existing settings
    chrome.storage.local.get(['profession', 'baseCv'], (result) => {
        if (result.profession) professionInput.value = result.profession;
        if (result.baseCv) baseCvInput.value = result.baseCv;
    });

    // Save settings
    saveBtn.addEventListener('click', () => {
        const profession = professionInput.value.trim();
        const baseCv = baseCvInput.value.trim();

        chrome.storage.local.set({ profession, baseCv }, () => {
            statusDiv.style.display = 'block';
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 2000);
        });
    });
});
