"""
web/fix_sidebar_nav.py
JobHunt Pro - Navigation links template sync helper utility
Automatically replaces/synchronizes dashboard shell sidebar navigation links
across English and Arabic templates layouts.
"""
import logging
import os
import re
import sys

# Configure logging
logger = logging.getLogger(__name__)

AR_SHELL: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates", "ar", "_dashboard_shell.html"))
EN_SHELL: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates", "en", "_dashboard_shell.html"))

# The new navigation links in Arabic
AR_NAV_HTML: str = """        <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
            <a href="/dashboard/v3" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'dashboard' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="layout-dashboard" class="w-5 h-5"></i>
                <span class="font-medium text-sm">لوحة القيادة</span>
            </a>
            
            <a href="/upload-cv" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'upload-cv' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="file-text" class="w-5 h-5"></i>
                <span class="font-medium text-sm">رفع السيرة الذاتية</span>
            </a>

            <a href="/ats-scorer" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'ats-scorer' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="target" class="w-5 h-5"></i>
                <span class="font-medium text-sm">مقياس ATS</span>
            </a>

            <a href="/resume-tailor" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'resume-tailor' else 'text-purple-400 hover:text-purple-300 hover:bg-white/5' }}">
                <i data-lucide="wand-2" class="w-5 h-5"></i>
                <span class="font-medium text-sm">تخصيص السيرة الذاتية</span>
            </a>

            <a href="/new-campaign" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'new-campaign' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="rocket" class="w-5 h-5"></i>
                <span class="font-medium text-sm">حملة جديدة</span>
            </a>

            <a href="/sent-emails" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'sent-emails' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="send" class="w-5 h-5"></i>
                <span class="font-medium text-sm">الرسائل المرسلة</span>
            </a>

            <a href="/funnel-analytics" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'funnel-analytics' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="bar-chart-2" class="w-5 h-5"></i>
                <span class="font-medium text-sm">تحليلات التوظيف</span>
            </a>

            <div class="my-4 border-t border-white/5"></div>

            <a href="/battle-station" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'battle-station' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="swords" class="w-5 h-5"></i>
                <span class="font-medium text-sm">محطة المعركة</span>
            </a>

            <a href="/services" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'services' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="star" class="w-5 h-5"></i>
                <span class="font-medium text-sm">الخدمات المميزة</span>
            </a>

            <a href="/wallet" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'wallet' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="wallet" class="w-5 h-5"></i>
                <span class="font-medium text-sm">المحفظة</span>
            </a>

            <a href="/my-purchases" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'my-purchases' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="package" class="w-5 h-5"></i>
                <span class="font-medium text-sm">اشتراكاتي</span>
            </a>

            <a href="/stats" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'stats' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="pie-chart" class="w-5 h-5"></i>
                <span class="font-medium text-sm">الإحصائيات</span>
            </a>

            <div class="my-4 border-t border-white/5"></div>

            <a href="/admin" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-red-500/10 text-red-400' if active_page == 'admin' else 'text-red-400/70 hover:text-red-400 hover:bg-red-500/5' }}">
                <i data-lucide="shield-alert" class="w-5 h-5"></i>
                <span class="font-medium text-sm">لوحة الإدارة</span>
            </a>
            
            <a href="/contact" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'contact' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="message-square" class="w-5 h-5"></i>
                <span class="font-medium text-sm">الدعم الفني</span>
            </a>
        </nav>"""

# The new navigation links in English
EN_NAV_HTML: str = """        <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
            <a href="/dashboard/v3" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'dashboard' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="layout-dashboard" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Dashboard</span>
            </a>
            
            <a href="/upload-cv" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'upload-cv' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="file-text" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Upload CV</span>
            </a>

            <a href="/ats-scorer" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'ats-scorer' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="target" class="w-5 h-5"></i>
                <span class="font-medium text-sm">ATS Scorer</span>
            </a>

            <a href="/resume-tailor" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'resume-tailor' else 'text-purple-400 hover:text-purple-300 hover:bg-white/5' }}">
                <i data-lucide="wand-2" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Resume Tailor</span>
            </a>

            <a href="/new-campaign" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'new-campaign' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="rocket" class="w-5 h-5"></i>
                <span class="font-medium text-sm">New Campaign</span>
            </a>

            <a href="/sent-emails" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'sent-emails' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="send" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Sent Emails</span>
            </a>

            <a href="/funnel-analytics" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'funnel-analytics' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="bar-chart-2" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Funnel Analytics</span>
            </a>

            <div class="my-4 border-t border-white/5"></div>

            <a href="/battle-station" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'battle-station' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="swords" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Battle Station</span>
            </a>

            <a href="/services" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'services' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="star" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Premium Services</span>
            </a>

            <a href="/wallet" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'wallet' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="wallet" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Wallet</span>
            </a>

            <a href="/my-purchases" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'my-purchases' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="package" class="w-5 h-5"></i>
                <span class="font-medium text-sm">My Purchases</span>
            </a>

            <a href="/stats" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'stats' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="pie-chart" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Statistics</span>
            </a>

            <div class="my-4 border-t border-white/5"></div>

            <a href="/admin" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-red-500/10 text-red-400' if active_page == 'admin' else 'text-red-400/70 hover:text-red-400 hover:bg-red-500/5' }}">
                <i data-lucide="shield-alert" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Admin Panel</span>
            </a>
            
            <a href="/contact" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all {{ 'bg-indigo-500/10 text-indigo-400' if active_page == 'contact' else 'text-slate-400 hover:text-white hover:bg-white/5' }}">
                <i data-lucide="message-square" class="w-5 h-5"></i>
                <span class="font-medium text-sm">Support</span>
            </a>
        </nav>"""

def replace_nav(file_path: str, new_nav: str) -> None:
    """Read the HTML shell template file and replace navigation markup safely."""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(r'<nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1">.*?</nav>', re.DOTALL)
        new_content = pattern.sub(new_nav, content)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        logger.info(f"Replaced nav in {file_path}")
    except Exception as e:
        logger.error(f"Failed to replace nav in {file_path}: {e}")
        raise

if __name__ == "__main__":
    try:
        replace_nav(AR_SHELL, AR_NAV_HTML)
        replace_nav(EN_SHELL, EN_NAV_HTML)
    except Exception as run_e:
        logger.error(f"Execution failed: {run_e}")
        sys.exit(1)
