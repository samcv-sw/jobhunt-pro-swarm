document.addEventListener('DOMContentLoaded', () => {
    const WEBHOOK_URL = "";  // Served by FastAPI — use local origin
    let tg;
    let userId = 'demo123';
    let currentLang = 'en';

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

    // Translations Dictionary
    const translations = {
        en: {
            title: "AI Resume Booster",
            desc: "Unlock our global AI swarm to automatically apply you to 500 remote jobs worldwide.",
            invites: "Invites",
            credits: "Credits",
            inviteBtn: "Invite 5 Friends (Free)",
            payBtn: "Unlock Now ($20 Crypto)",
            payBtnFree: "Launch Swarm (Free)",
            divider: "OR",
            footer: "Powered by Advanced AI Swarm Tech",
            launching: "Launching Swarm...",
            generating: "Generating Crypto Invoice...",
            alertLaunched: "Swarm Launched! Check your bot for live updates.",
            alertFailed: "Failed to launch.",
            alertInvoiceFailed: "Failed to generate invoice. Please try again.",
            alertError: "Error connecting to payment gateway: "
        },
        ar: {
            title: "داعم السيرة الذاتية بالذكاء الاصطناعي",
            desc: "قم بتفعيل سرب الذكاء الاصطناعي العالمي للتقديم التلقائي على 500 وظيفة عن بعد حول العالم.",
            invites: "الدعوات",
            credits: "النقاط",
            inviteBtn: "دعوة 5 أصدقاء (مجانًا)",
            payBtn: "تفعيل الآن (20$ بالعملات الرقمية)",
            payBtnFree: "إطلاق السرب الذكي (مجانًا)",
            divider: "أو",
            footer: "مشغّل بواسطة تقنية أسراب الذكاء الاصطناعي المتقدمة",
            launching: "جاري إطلاق السرب...",
            generating: "جاري إنشاء فاتورة العملات الرقمية...",
            alertLaunched: "تم إطلاق السرب بنجاح! راقب التحديثات من خلال البوت.",
            alertFailed: "فشل في إطلاق السرب.",
            alertInvoiceFailed: "فشل في إنشاء الفاتورة. الرجاء المحاولة مرة أخرى.",
            alertError: "خطأ في الاتصال ببوابة الدفع: "
        },
        es: {
            title: "Potenciador de CV con IA",
            desc: "Desbloquea nuestro enjambre global de IA para postularte automáticamente a 500 empleos remotos en todo el mundo.",
            invites: "Invitaciones",
            credits: "Créditos",
            inviteBtn: "Invitar a 5 amigos (Gratis)",
            payBtn: "Desbloquear ahora ($20 Crypto)",
            payBtnFree: "Lanzar enjambre (Gratis)",
            divider: "O",
            footer: "Desarrollado por tecnología avanzada de enjambre de IA",
            launching: "Lanzando enjambre...",
            generating: "Generando factura criptográfica...",
            alertLaunched: "¡Enjambre lanzado! Consulta tu bot para actualizaciones en vivo.",
            alertFailed: "Error al lanzar.",
            alertInvoiceFailed: "No se pudo generar la factura. Inténtalo de nuevo.",
            alertError: "Error al conectar con la pasarela de pago: "
        },
        hi: {
            title: "एआई रिज्यूमे बूस्टर",
            desc: "दुनिया भर में 500 रिमोट नौकरियों में स्वचालित रूप से आवेदन करने के लिए हमारे वैश्विक एआई झुंड को अनलॉक करें।",
            invites: "आमंत्रण",
            credits: "क्रेडिट",
            inviteBtn: "5 मित्रों को आमंत्रित करें (मुफ़्त)",
            payBtn: "अभी अनलॉक करें ($20 क्रिप्टो)",
            payBtnFree: "झुंड लॉन्च करें (मुफ़्त)",
            divider: "या",
            footer: "उन्नत एआई झुंड तकनीक द्वारा संचालित",
            launching: "झुंड लॉन्च हो रहा है...",
            generating: "क्रिप्टो चालान उत्पन्न किया जा रहा है...",
            alertLaunched: "झुंड लॉन्च हो गया! लाइव अपडेट के लिए अपने बॉट की जांच करें।",
            alertFailed: "लॉंच करने में विफल।",
            alertInvoiceFailed: "चालान जनरेट करने में विफल। कृपया पुन: प्रयास करें।",
            alertError: "पेमेंट गेटवे से कनेक्ट करने में त्रुटि: "
        },
        ru: {
            title: "ИИ Ускоритель Резюме",
            desc: "Разблокируйте наш глобальный рой ИИ для автоматической подачи заявок на 500 удаленных вакансий по всему миру.",
            invites: "Приглашения",
            credits: "Кредиты",
            inviteBtn: "Пригласить 5 друзей (Бесплатно)",
            payBtn: "Разблокировать сейчас ($20 Крипто)",
            payBtnFree: "Запустить Рой (Бесплатно)",
            divider: "ИЛИ",
            footer: "Работает на передовой технологии ИИ Роя",
            launching: "Запуск роя...",
            generating: "Создание счета на криптовалюту...",
            alertLaunched: "Рой запущен! Следите за обновлениями в боте.",
            alertFailed: "Не удалось запустить.",
            alertInvoiceFailed: "Не удалось создать счет. Попробуйте еще раз.",
            alertError: "Ошибка подключения к платежному шлюзу: "
        },
        pt: {
            title: "Impulsionador de Currículo IA",
            desc: "Desbloqueie nosso enxame global de IA para se candidatar automaticamente a 500 vagas remotas em todo o mundo.",
            invites: "Convites",
            credits: "Créditos",
            inviteBtn: "Convidar 5 amigos (Grátis)",
            payBtn: "Desbloquear agora ($20 Crypto)",
            payBtnFree: "Iniciar enxame (Grátis)",
            divider: "OU",
            footer: "Desenvolvido por tecnologia avançada de enxame de IA",
            launching: "Iniciando enxame...",
            generating: "Gerando fatura cripto...",
            alertLaunched: "Enxame lançado! Verifique seu bot para atualizações ao vivo.",
            alertFailed: "Falha ao iniciar.",
            alertInvoiceFailed: "Falha ao gerar fatura. Tente novamente.",
            alertError: "Erro ao conectar ao gateway de pagamento: "
        }
    };

    // Apply Language Function
    function applyLanguage(lang) {
        currentLang = lang;
        const dict = translations[lang] || translations.en;
        
        // Update document direction
        if (lang === 'ar') {
            document.documentElement.setAttribute('dir', 'rtl');
            document.body.setAttribute('dir', 'rtl');
            document.documentElement.style.setProperty('--text-x-direction', '-1');
        } else {
            document.documentElement.setAttribute('dir', 'ltr');
            document.body.setAttribute('dir', 'ltr');
            document.documentElement.style.setProperty('--text-x-direction', '1');
        }

        // Apply text updates
        document.getElementById('app-title').innerText = dict.title;
        document.getElementById('app-desc').innerText = dict.desc;
        document.getElementById('label-invites').innerText = dict.invites;
        document.getElementById('label-credits').innerText = dict.credits;
        document.getElementById('invite-btn-text').innerText = dict.inviteBtn;
        document.getElementById('divider-text').innerText = dict.divider;
        document.getElementById('footer-text').innerText = dict.footer;

        // Apply pay button updates (handling state dynamic text)
        const payBtn = document.getElementById('pay-btn');
        const payTextSpan = document.getElementById('pay-btn-text');
        if (payTextSpan) {
            if (payBtn.dataset.free === 'true') {
                payTextSpan.innerText = dict.payBtnFree;
            } else {
                payTextSpan.innerText = dict.payBtn;
            }
        }
    }

    // Set default language based on user device/Telegram preferences if possible
    try {
        const tgLang = window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code;
        if (tgLang && translations[tgLang]) {
            document.getElementById('langSelect').value = tgLang;
            applyLanguage(tgLang);
        } else {
            applyLanguage('en');
        }
    } catch(e) {
        applyLanguage('en');
    }

    // Handle Language Select Changes
    document.getElementById('langSelect').addEventListener('change', (e) => {
        applyLanguage(e.target.value);
    });

    // Fetch User Stats
    async function fetchStats() {
        try {
            const res = await fetch(`${WEBHOOK_URL}/api/v1/user/${userId}`);
            if (!res.ok || !res.headers.get('content-type')?.includes('application/json')) {
                console.log("Using local/fallback stats (API offline or not returning JSON)");
                return;
            }
            const data = await res.ok ? await res.json() : {};
            const credits = data.credits || 0;
            document.getElementById('invite-count').innerText = `${credits}/3`;
            document.getElementById('credit-count').innerText = credits;
            
            if (credits >= 3) {
                const payBtn = document.getElementById('pay-btn');
                payBtn.closest('button').dataset.free = 'true';
                payBtn.classList.remove('secondary');
                payBtn.classList.add('primary');
                applyLanguage(currentLang);
            }
        } catch(e) {
            console.log("Failed to fetch stats:", e.message);
        }
    }
    fetchStats();

    // Invite Button Logic (Virality)
    document.getElementById('invite-btn').addEventListener('click', () => {
        const botUsername = "JobHuntPro_Ai_Bot"; // The actual bot username
        let user_id = tg?.initDataUnsafe?.user?.id || 'demo123';
        const inviteLink = `https://t.me/${botUsername}?start=${user_id}`;
        
        const shareText = currentLang === 'ar' 
            ? `🚀 أنا أستخدم JobHunt Pro بالذكاء الاصطناعي للتقديم التلقائي على 500 وظيفة! احصل عليه مجاناً هنا:`
            : `🚀 I'm using JobHunt Pro AI to automatically apply for 500 jobs! Get it free here:`;
        
        const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(inviteLink)}&text=${encodeURIComponent(shareText)}`;
        
        if (tg && tg.openTelegramLink) {
            tg.openTelegramLink(shareUrl);
        } else {
            window.open(shareUrl, '_blank');
        }
    });

    // Pay/Launch Button Logic (Monetization / Engagement)
    document.getElementById('pay-btn').addEventListener('click', async (e) => {
        const payBtn = e.target.closest('button');
        const isFree = payBtn.dataset.free === 'true';
        const dict = translations[currentLang] || translations.en;

        if (isFree) {
            tg?.MainButton.setText(dict.launching);
            tg?.MainButton.show();
            
            // Deduct credits and launch
            try {
                await fetch(`${WEBHOOK_URL}/api/v1/queue/status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ telegram_id: userId, status: 'queued' })
                });
                if (tg && tg.showAlert) {
                    tg.showAlert(dict.alertLaunched);
                } else {
                    alert(dict.alertLaunched);
                }
                tg?.close();
            } catch (err) {
                if (tg && tg.showAlert) {
                    tg.showAlert(dict.alertFailed);
                } else {
                    alert(dict.alertFailed);
                }
            }
            tg?.MainButton.hide();
            return;
        }

        tg?.MainButton.setText(dict.generating);
        tg?.MainButton.show();
        
        try {
            const response = await fetch(`${WEBHOOK_URL}/api/v1/tma/checkout`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userId: userId })
            });
            
            const data = await response.json();
            tg?.MainButton.hide();
            
            if (data.invoice_url) {
                if (tg && tg.openLink) {
                    tg.openLink(data.invoice_url);
                } else {
                    window.location.href = data.invoice_url;
                }
            } else {
                if (tg && tg.showAlert) {
                    tg.showAlert(dict.alertInvoiceFailed);
                } else {
                    alert(dict.alertInvoiceFailed);
                }
            }
        } catch (err) {
            tg?.MainButton.hide();
            const errMsg = dict.alertError + err.message;
            if (tg && tg.showAlert) {
                tg.showAlert(errMsg);
            } else {
                alert(errMsg);
            }
        }
    });
});
