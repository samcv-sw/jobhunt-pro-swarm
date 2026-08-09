/**
 * Sovereign Multi-Lingual & RTL/LTR Engine for JobHunt Pro.
 * Provides client-side dynamic localization, direction switching, and locale persistence.
 */

const JobHuntI18n = {
  currentLocale: (() => {
    const localLang = localStorage.getItem('jh_locale');
    if (localLang && localLang.length <= 10) return localLang.toLowerCase();
    const cookieMatch = document.cookie.match(/(?:^|;\s*)lang=([^;]+)/);
    if (cookieMatch && cookieMatch[1].length <= 10) return cookieMatch[1].toLowerCase();
    const urlLang = new URLSearchParams(window.location.search).get('lang');
    if (urlLang && urlLang.length <= 10) return urlLang.toLowerCase();
    const docLang = document.documentElement.getAttribute('lang');
    if (docLang && docLang.length <= 10) return docLang.toLowerCase();
    return 'ar';
  })(),
  
  translations: {
    ar: {
      dir: 'rtl',
      font: "'Cairo', 'Tajawal', sans-serif",
      dashboard: 'لوحة التحكم الرئيسية',
      auto_applier: 'نظام التقديم الآلي',
      mock_interview: 'المقابلة الصوتية بالذكاء الاصطناعي',
      ats_score: 'نسبة التوافق مع ATS',
      status_active: 'نشط ويعمل',
      apply_now: 'تقديم سريع الآن'
    },
    en: {
      dir: 'ltr',
      font: "'Inter', system-ui, sans-serif",
      dashboard: 'Sovereign Dashboard',
      auto_applier: 'Autonomous Auto-Applier',
      mock_interview: 'AI Voice Mock Interview',
      ats_score: 'ATS Match Score',
      status_active: 'Active & Running',
      apply_now: 'Apply Now'
    },
    fr: {
      dir: 'ltr',
      font: "'Inter', system-ui, sans-serif",
      dashboard: 'Tableau de Bord',
      auto_applier: 'Candidature Automatique',
      mock_interview: 'Entretien Vocal IA',
      ats_score: 'Score de Match ATS',
      status_active: 'Actif et opérationnel',
      apply_now: 'Postuler Maintenant'
    },
    zh: {
      dir: 'ltr',
      font: "'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif",
      dashboard: '控制台',
      auto_applier: '自动投递系统',
      mock_interview: 'AI 语音模拟面试',
      ats_score: 'ATS 匹配度得分',
      status_active: '运行中',
      apply_now: '立即申请'
    }
  },

  init() {
    this.setLocale(this.currentLocale);
  },

  setLocale(lang) {
    if (!lang || typeof lang !== 'string') lang = 'ar';
    const cleanCode = lang.split('-')[0].toLowerCase();

    this.currentLocale = lang;
    localStorage.setItem('jh_locale', lang);

    const rtlLangs = ['ar', 'fa', 'ur', 'he', 'ps', 'sd', 'yi'];
    const isRtl = rtlLangs.includes(cleanCode);

    const config = this.translations[cleanCode] || {
      dir: isRtl ? 'rtl' : 'ltr',
      font: isRtl ? "'Cairo', 'Tajawal', sans-serif" : "'Inter', system-ui, sans-serif"
    };

    document.documentElement.setAttribute('lang', lang);
    document.documentElement.setAttribute('dir', config.dir);
    if (document.body) {
      document.body.style.fontFamily = config.font;
    }

    // Dispatch global event for listeners
    window.dispatchEvent(new CustomEvent('localeChange', { detail: { lang, config } }));
  },

  t(key) {
    const dict = this.translations[this.currentLocale] || this.translations['ar'];
    return dict[key] || key;
  }
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => JobHuntI18n.init());
} else {
  JobHuntI18n.init();
}