document.addEventListener('DOMContentLoaded', () => {
    // Initialize Telegram Web App SDK
    let tg;
    try {
        tg = window.Telegram.WebApp;
        tg.expand(); // Expand to full screen
        
        // Setup user info
        const user = tg.initDataUnsafe?.user;
        if (user) {
            document.getElementById('user-greeting').innerText = `Welcome, ${user.first_name}!`;
        }
    } catch (e) {
        console.log("Not running inside Telegram");
    }

    // Invite Button Logic (Virality)
    document.getElementById('invite-btn').addEventListener('click', () => {
        const botUsername = "JobHuntPro_Ai_Bot"; // The actual bot username
        let userId = tg?.initDataUnsafe?.user?.id || 'demo123';
        const inviteLink = `https://t.me/${botUsername}?start=${userId}`;
        
        const shareText = `🚀 I'm using JobHunt Pro AI to automatically apply for 500 jobs! Get it free here:`;
        const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(inviteLink)}&text=${encodeURIComponent(shareText)}`;
        
        if (tg && tg.openTelegramLink) {
            tg.openTelegramLink(shareUrl);
        } else {
            window.open(shareUrl, '_blank');
        }
    });

    // Pay Button Logic (Monetization)
    document.getElementById('pay-btn').addEventListener('click', async () => {
        let userId = tg?.initDataUnsafe?.user?.id || 'demo123';
        
        tg?.MainButton.setText("Generating Crypto Invoice...");
        tg?.MainButton.show();
        
        try {
            const response = await fetch("https://olympus-webhook.samsalameh-cv.workers.dev/api/v1/checkout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userId: userId })
            });
            
            const data = await response.json();
            tg?.MainButton.hide();
            
            if (data.invoice_url) {
                // Redirect user to NOWPayments checkout page
                if (tg && tg.openLink) {
                    tg.openLink(data.invoice_url);
                } else {
                    window.location.href = data.invoice_url;
                }
            } else {
                tg?.showAlert("Failed to generate invoice. Please try again.");
            }
        } catch (e) {
            tg?.MainButton.hide();
            tg?.showAlert("Error connecting to payment gateway: " + e.message);
        }
    });
});
