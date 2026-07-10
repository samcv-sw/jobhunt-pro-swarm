import os
import re

def refactor_dashboard(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Hero
    content = re.sub(
        r'class="relative overflow-hidden rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-slate-900/80 to-slate-800/90 p-8 shadow-2xl backdrop-blur-xl reveal"',
        r'class="glass-panel relative overflow-hidden p-8 reveal"',
        content
    )
    
    # SMTP Banner
    content = re.sub(
        r'class="flex flex-col items-start justify-between gap-4 rounded-xl border border-emerald-500/30 border-l-4 border-l-emerald-500 bg-emerald-500/10 p-6 sm:flex-row sm:items-center reveal"',
        r'class="glass-panel border-l-4 border-l-emerald-500 p-6 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center reveal"',
        content
    )

    # Stat Cards
    for i, color in enumerate(['indigo', 'emerald', 'pink', 'amber'], 1):
        pattern = fr'class="rounded-xl border border-white/5 bg-slate-900/50 p-5 backdrop-blur-md transition-all hover:-translate-y-1 hover:border-{color}-500/30 hover:bg-slate-800/50 hover:shadow-lg hover:shadow-{color}-500/10 reveal"'
        replacement = f'class="glass-panel stat-card p-5 reveal"'
        content = re.sub(pattern, replacement, content)

    # Main columns
    content = re.sub(
        r'class="rounded-xl border border-white/5 bg-slate-900/50 p-6 backdrop-blur-md lg:col-span-2 reveal"',
        r'class="glass-panel p-6 lg:col-span-2 reveal"',
        content
    )
    content = re.sub(
        r'class="rounded-xl border border-white/5 bg-slate-900/50 p-6 backdrop-blur-md reveal"',
        r'class="glass-panel p-6 reveal"',
        content
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

base_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"
refactor_dashboard(os.path.join(base_dir, "dashboard_v3.html"))
refactor_dashboard(os.path.join(base_dir, "en", "dashboard_v3.html"))

logger.debug("Dashboard templates refactored!")
