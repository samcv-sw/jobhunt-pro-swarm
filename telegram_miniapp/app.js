document.addEventListener('DOMContentLoaded', () => {
    const WEBHOOK_URL = "https://olympus-webhook.samsalameh-cv.workers.dev";
    let tg;
    let userId = 'demo123';
    try {
        tg = window.Telegram.WebApp;
        tg.expand(); // Expand to full screen
        
        // Setup user info
        const user = tg.initDataUnsafe?.user;
        if (user) {
            userId = user.id;
            const greetingEl = document.getElementById('user-greeting');
            if (greetingEl) {
                greetingEl.innerText = `Welcome, ${user.first_name}!`;
            }
        }
    } catch (e) {
        console.log("Not running inside Telegram");
    }

    // Fetch User Stats
    async function fetchStats() {
        try {
            const res = await fetch(`${WEBHOOK_URL}/api/v1/user/${userId}`);
            if (!res.ok || !res.headers.get('content-type')?.includes('application/json')) {
                console.log("Using local/fallback stats (API offline or not returning JSON)");
                return;
            }
            const data = await res.json();
            const credits = data.credits || 0;
            document.getElementById('invite-count').innerText = `${credits}/3`;
            document.getElementById('credit-count').innerText = credits;
            
            if (credits >= 3) {
                const payBtn = document.getElementById('pay-btn');
                payBtn.innerHTML = `<span class="btn-icon">🚀</span> Launch Swarm (Free)`;
                payBtn.classList.remove('secondary');
                payBtn.classList.add('primary');
                payBtn.dataset.free = 'true';
            }
        } catch(e) {
            console.log("Failed to fetch stats:", e.message);
        }
    }
    fetchStats();

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
    document.getElementById('pay-btn').addEventListener('click', async (e) => {
        if (e.target.closest('button').dataset.free === 'true') {
            tg?.MainButton.setText("Launching Swarm...");
            tg?.MainButton.show();
            
            // Deduct credits and launch
            try {
                // We'll call a quick free-launch endpoint
                await fetch(`${WEBHOOK_URL}/api/v1/queue/status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ telegram_id: userId, status: 'queued' })
                });
                tg?.showAlert("Swarm Launched! Check your bot for live updates.");
                tg?.close();
            } catch (err) {
                tg?.showAlert("Failed to launch.");
            }
            tg?.MainButton.hide();
            return;
        }

        tg?.MainButton.setText("Generating Crypto Invoice...");
        tg?.MainButton.show();
        
        try {
            const response = await fetch(`${WEBHOOK_URL}/api/v1/checkout`, {
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
        } catch (err) {
            tg?.MainButton.hide();
            tg?.showAlert("Error connecting to payment gateway: " + err.message);
        }
    });
});
