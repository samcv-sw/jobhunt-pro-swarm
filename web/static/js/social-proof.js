/**
 * JobHunt Pro — Growth & Real-time Social Proof Engine
 * Lightweight, non-intrusive activity toast notifications.
 */
(function() {
    'use strict';

    const fallbackEvents = [
        { name: 'أحمد .م (الرياض)', action: 'قام بتفعيل باقة الاحتراف ⚡', time: 'منذ دقيقتين' },
        { name: 'John D. (Dubai)', action: 'Launched 50 Automated B2B Campaigns 🚀', time: '3 mins ago' },
        { name: 'سارة .ك (جدة)', action: 'أرسلت 120 طلب توظيف آلي 🎯', time: 'منذ 5 دقائق' },
        { name: 'Tariq A. (Abu Dhabi)', action: 'Upgraded to Enterprise AI Swarm 💼', time: '7 mins ago' },
        { name: 'عمر .ب (الكويت)', action: 'حصل على 3 مقابلات عمل هذا الأسبوع 🏆', time: 'منذ 10 دقائق' }
    ];

    let eventsQueue = [];
    let currentIndex = 0;

    function createToastContainer() {
        if (document.getElementById('jh-social-proof-container')) return;

        const style = document.createElement('style');
        style.textContent = `
            #jh-social-proof-container {
                position: fixed;
                inset-block-end: 20px;
                inset-inline-start: 20px;
                z-index: 9999;
                pointer-events: none;
                font-family: 'Cairo', system-ui, sans-serif;
            }
            .jh-social-toast {
                pointer-events: auto;
                display: flex;
                align-items: center;
                gap: 12px;
                background: rgba(15, 23, 42, 0.88);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(59, 130, 246, 0.3);
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 12px 16px;
                max-width: 340px;
                color: #f8fafc;
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            }
            .jh-social-toast.visible {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
            .jh-toast-badge {
                width: 38px;
                height: 38px;
                border-radius: 50%;
                background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                flex-shrink: 0;
                box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
            }
            .jh-toast-content {
                display: flex;
                flex-direction: column;
                gap: 2px;
            }
            .jh-toast-name {
                font-weight: 700;
                font-size: 13px;
                color: #60a5fa;
            }
            .jh-toast-action {
                font-size: 12px;
                color: #e2e8f0;
                line-height: 1.4;
            }
            .jh-toast-time {
                font-size: 11px;
                color: #94a3b8;
                margin-block-start: 2px;
            }
        `;
        document.head.appendChild(style);

        const container = document.createElement('div');
        container.id = 'jh-social-proof-container';
        document.body.appendChild(container);
    }

    async function loadProofData() {
        try {
            const resp = await fetch('/api/social-proof');
            if (resp.ok) {
                const data = await resp.json();
                if (data.success && data.purchases && data.purchases.length > 0) {
                    eventsQueue = data.purchases.map(p => ({
                        name: p.name || 'مستخدم جديد',
                        action: `اشترى باقة ${p.package_name || 'الاحتراف'} بقيمة $${p.amount_usd || 10} ✨`,
                        time: 'حديثاً'
                    }));
                }
            }
        } catch (e) {
            // Silently fallback to synthetic proof items
        }
        if (!eventsQueue || eventsQueue.length === 0) {
            eventsQueue = fallbackEvents;
        }
    }

    function showNextToast() {
        const container = document.getElementById('jh-social-proof-container');
        if (!container || eventsQueue.length === 0) return;

        const evt = eventsQueue[currentIndex % eventsQueue.length];
        currentIndex++;

        const toast = document.createElement('div');
        toast.className = 'jh-social-toast';
        toast.innerHTML = `
            <div class="jh-toast-badge">🔥</div>
            <div class="jh-toast-content">
                <div class="jh-toast-name">${evt.name}</div>
                <div class="jh-toast-action">${evt.action}</div>
                <div class="jh-toast-time">${evt.time}</div>
            </div>
        `;

        container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('visible');
        });

        // Remove after 4.5 seconds
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => {
                toast.remove();
            }, 400);
        }, 4500);
    }

    function init() {
        createToastContainer();
        loadProofData().then(() => {
            // First toast after 3 seconds
            setTimeout(showNextToast, 3000);
            // Repeat every 14 seconds
            setInterval(showNextToast, 14000);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
