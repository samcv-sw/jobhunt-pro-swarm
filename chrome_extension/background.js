chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "apply_via_ai") {
        // Here we hit our FastAPI backend
        // In production, we would use the actual deployed URL (e.g., render.com)
        // We assume the user is logged in via session cookie or API key stored in chrome.storage
        
        chrome.storage.local.get(['api_key'], function(result) {
            const apiKey = result.api_key || "dummy_key_for_now";
            
            fetch("http://127.0.0.1:8000/api/v1/extension/apply", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": apiKey
                },
                body: JSON.stringify(request.data)
            })
            .then(res => res.json())
            .then(data => {
                console.log("Successfully queued via extension:", data);
            })
            .catch(err => {
                console.error("Extension API Error:", err);
            });
        });
    }
});
