"""
JobHunt Pro — UI Text Translation Seeder
Populates initial UI text translations across 12 major global languages.
"""

import asyncio
import logging
import sys
from sqlalchemy import select
from backend.database import engine, Base, async_session
from backend.models import UITextTranslation

# Setup structured logging for database seeding
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("seed_translations")

# UI text translations for 12 languages
UI_TEXT_TRANSLATIONS = {
    "en": {
        "welcome_message": "Welcome to JobHunt Pro",
        "job_listing": "Job Listing",
        "apply_button": "Apply Now",
        "filter_jobs": "Filter Jobs",
        "no_jobs_found": "No jobs found",
        "login": "Login",
        "signup": "Sign Up",
        "reset_password": "Reset Password",
        "terms_of_service": "Terms of Service",
        "privacy_policy": "Privacy Policy",
        "contact_us": "Contact Us",
    },
    "ar": {
        "welcome_message": "مرحبا بكم في JobHunt برو",
        "job_listing": "إعلان وظيفة",
        "apply_button": "تقديم الآن",
        "filter_jobs": "تصفية الوظائف",
        "no_jobs_found": "لم يتم العثور على وظائف",
        "login": "تسجيل الدخول",
        "signup": "إنشاء حساب",
        "reset_password": "إعادة تعيين كلمة المرور",
        "terms_of_service": "شروط الخدمة",
        "privacy_policy": "سياسة الخصوصية",
        "contact_us": "اتصل بنا",
    },
    "fr": {
        "welcome_message": "Bienvenue sur JobHunt Pro",
        "job_listing": "Offre d'emploi",
        "apply_button": "Postuler",
        "filter_jobs": "Filtrer les emplois",
        "no_jobs_found": "Aucun emploi trouvé",
        "login": "Connexion",
        "signup": "S'inscrire",
        "reset_password": "Réinitialiser le mot de passe",
        "terms_of_service": "Conditions d'utilisation",
        "privacy_policy": "Politique de confidentialité",
        "contact_us": "Contactez-nous",
    },
    "es": {
        "welcome_message": "Bienvenido a JobHunt Pro",
        "job_listing": "Oferta de empleo",
        "apply_button": "Postularse",
        "filter_jobs": "Filtrar empleos",
        "no_jobs_found": "No se encontraron empleos",
        "login": "Iniciar sesión",
        "signup": "Registrarse",
        "reset_password": "Restablecer contraseña",
        "terms_of_service": "Términos del servicio",
        "privacy_policy": "Política de privacidad",
        "contact_us": "Contáctanos",
    },
    "de": {
        "welcome_message": "Willkommen bei JobHunt Pro",
        "job_listing": "Stellenanzeige",
        "apply_button": "Jetzt bewerben",
        "filter_jobs": "Stellen filtern",
        "no_jobs_found": "Keine Stellen gefunden",
        "login": "Einloggen",
        "signup": "Registrieren",
        "reset_password": "Passwort zurücksetzen",
        "terms_of_service": "Nutzungsbedingungen",
        "privacy_policy": "Datenschutzbestimmung",
        "contact_us": "Kontaktieren Sie uns",
    },
    "zh": {
        "welcome_message": "欢迎使用 JobHunt Pro",
        "job_listing": "职位发布",
        "apply_button": "立即申请",
        "filter_jobs": "筛选职位",
        "no_jobs_found": "未找到职位",
        "login": "登录",
        "signup": "注册",
        "reset_password": "重置密码",
        "terms_of_service": "服务条款",
        "privacy_policy": "隐私政策",
        "contact_us": "联系我们",
    },
    "ja": {
        "welcome_message": "JobHunt Proへようこそ",
        "job_listing": "求人情報",
        "apply_button": "今すぐ応募",
        "filter_jobs": "求人を絞り込む",
        "no_jobs_found": "求人が見つかりません",
        "login": "ログイン",
        "signup": "サインアップ",
        "reset_password": "パスワードリセット",
        "terms_of_service": "利用規約",
        "privacy_policy": "プライバシーポリシー",
        "contact_us": "お問い合わせ",
    },
    "ru": {
        "welcome_message": "Добро пожаловать в JobHunt Pro",
        "job_listing": "Вакансия",
        "apply_button": "Подать заявку",
        "filter_jobs": "Фильтровать вакансии",
        "no_jobs_found": "Вакансий не найдено",
        "login": "Войти",
        "signup": "Регистрация",
        "reset_password": "Сброс пароля",
        "terms_of_service": "Условия использования",
        "privacy_policy": "Политика конфиденциальности",
        "contact_us": "Свяжитесь с нами",
    },
    "pt": {
        "welcome_message": "Bem-vindo ao JobHunt Pro",
        "job_listing": "Vaga de Emprego",
        "apply_button": "Aplicar Agora",
        "filter_jobs": "Filtrar Vagas",
        "no_jobs_found": "Nenhuma vaga encontrada",
        "login": "Entrar",
        "signup": "Inscrever-se",
        "reset_password": "Redefinir Senha",
        "terms_of_service": "Termos de Serviço",
        "privacy_policy": "Política de Privacidade",
        "contact_us": "Contate-nos",
    },
    "hi": {
        "welcome_message": "JobHunt Pro में स्वागत है",
        "job_listing": "रोजगार सूचना",
        "apply_button": "अभी आवेदन करें",
        "filter_jobs": "रोजगार फ़िल्टर करें",
        "no_jobs_found": "कोई नौकरी नहीं मिली",
        "login": "लॉग इन करें",
        "signup": "साइन अप करें",
        "reset_password": "पासवर्ड रीसेट करें",
        "terms_of_service": "सेवा नियम",
        "privacy_policy": "गोपनीयता नीति",
        "contact_us": "संपर्क करें",
    },
    "it": {
        "welcome_message": "Benvenuto su JobHunt Pro",
        "job_listing": "Offerta di Lavoro",
        "apply_button": "Candidati Subito",
        "filter_jobs": "Filtra Lavori",
        "no_jobs_found": "Nessun lavoro trovato",
        "login": "Accedi",
        "signup": "Registrati",
        "reset_password": "Reimposta Password",
        "terms_of_service": "Termini di Servizio",
        "privacy_policy": "Informativa sulla Privacy",
        "contact_us": "Contattaci",
    },
    "tr": {
        "welcome_message": "JobHunt Pro'ya Hoş Geldiniz",
        "job_listing": "İş İlanı",
        "apply_button": "Hemen Başvur",
        "filter_jobs": "İşleri Filtrele",
        "no_jobs_found": "İş bulunamadı",
        "login": "Giriş Yap",
        "signup": "Kaydol",
        "reset_password": "Şifreyi Sıfırla",
        "terms_of_service": "Hizmet Şartları",
        "privacy_policy": "Gizlilik Politikası",
        "contact_us": "Bize Ulaşın"
    },
}


async def seed_translations() -> None:
    """CreatesUITextTranslation tables if they do not exist and seeds initial translation matrix."""
    logger.info("Initializing database migrations and tables for translations...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("UITextTranslation table ensured.")
    except Exception as e:
        logger.error(f"Error ensuring translation table schema: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Running database translation seeder...")
    try:
        async with async_session() as session:
            result = await session.execute(select(UITextTranslation))
            existing = {(t.language_code, t.key) for t in result.scalars().all()}
            added = 0
            for lang, texts in UI_TEXT_TRANSLATIONS.items():
                for key, value in texts.items():
                    if (lang, key) in existing:
                        continue
                    session.add(UITextTranslation(key=key, language_code=lang, value=value))
                    added += 1
            await session.commit()
            logger.info(f"Seeded {added} new UI text translations across {len(UI_TEXT_TRANSLATIONS)} languages.")
    except Exception as e:
        logger.error(f"Failed to seed translations to target database: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_translations())