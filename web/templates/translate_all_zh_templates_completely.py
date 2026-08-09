import os
import re

zh_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\zh"

# Comprehensive UI & template translation mapping
UI_TRANSLATIONS = {
    # Nav, Shell & Common CTAs
    r'>\s*Command Center\s*<': '>指挥控制中心<',
    r'>\s*Engage Free\s*<': '>免费开启体验<',
    r'>\s*Get Started Free ↗\s*<': '>免费立即开始 ↗<',
    r'>\s*Get Started Free\s*<': '>免费立即开始<',
    r'>\s*Tech Support\s*<': '>技术支持与客服<',
    r'>\s*Tailor Resume\s*<': '>智能生成专属简历<',
    r'>\s*AI Interview Copilot\s*<': '>AI 实时面试辅导<',
    r'>\s*Compare\s*<': '>平台对比<',
    r'>\s*Privacy\s*<': '>隐私政策<',
    r'>\s*Terms\s*<': '>服务条款<',
    r'Built with ❤️ for job seekers worldwide\.': '用 ❤️ 为全球求职者打造。',
    
    # Zero Unemployment & Blueprint System
    r'Even if you have zero prior experience or no idea where to start\.\.\. enter your target monthly/daily income or select your scenario, and AI will generate real job opportunities and an instant CV blueprint!': '即使您零经验或不知道从何开始… 输入您的目标月薪/日薪或选择您的现状，AI 智能体将生成真实工作机会与即时 CV 蓝图！',
    r'💰 1\. Enter Your Target Income / Money to Earn:': '💰 1. 输入您的目标期望收入 / 想要赚取的薪资：',
    r'🎓 2\. Select Your Current Situation / Background:': '🎓 2. 选择您当前的求职现状 / 背景：',
    r'🤝 Low-Income Support': '🤝 低收入帮助与就业支持',
    r'✨ AI analyzing high-yield opportunities matching your target income &amp; background\.\.\.': '✨ AI 正在分析匹配您目标薪资与背景的高收益机会...',
    r'✨ AI analyzing high-yield opportunities matching your target income & background\.\.\.': '✨ AI 正在分析匹配您目标薪资与背景的高收益机会...',
    r'Remote WhatsApp &amp; Social Support Agent': '远程 WhatsApp 与社媒客服专员',
    r'Remote WhatsApp & Social Support Agent': '远程 WhatsApp 与社媒客服专员',

    # Sidebar & Menu Labels
    r'>\s*Dashboard\s*<': '>控制台<',
    r'>\s*Auto Applier\s*<': '>自动投递系统<',
    r'>\s*ATS Analyzer\s*<': '>ATS 简历优化器<',
    r'>\s*Resume Tailor\s*<': '>简历定制工具<',
    r'>\s*Interview Prep\s*<': '>面试准备与辅导<',
    r'>\s*Salary Negotiator\s*<': '>智能薪资谈判助手<',
    r'>\s*War Room\s*<': '>求职作战指挥室<',
    r'>\s*Battle Station\s*<': '>全自动工作站<',
    r'>\s*Analytics\s*<': '>数据统计分析<',
    r'>\s*My Purchases\s*<': '>我的已购服务<',
    r'>\s*Settings\s*<': '>账号与偏好设置<',

    # Common Card & Table Headings
    r'>\s*Overview\s*<': '>概览<',
    r'>\s*Active Campaigns\s*<': '>进行中的求职计划<',
    r'>\s*Recent Applications\s*<': '>近期投递记录<',
    r'>\s*Recommended Jobs\s*<': '>推荐适合职位<',
    r'>\s*Application History\s*<': '>历史投递列表<',
    r'>\s*Status\s*<': '>当前状态<',
    r'>\s*Actions\s*<': '>操作选项<',
    r'>\s*View Details\s*<': '>查看详细内容<',
    r'>\s*View All\s*<': '>查看全部<',
    r'>\s*Export Data\s*<': '>导出数据<',

    # Badges & Statuses
    r'>\s*Active\s*<': '>活跃运行中<',
    r'>\s*Pending\s*<': '>等待处理中<',
    r'>\s*Completed\s*<': '>已成功完成<',
    r'>\s*Failed\s*<': '>投递未成功<',
    r'>\s*Sent\s*<': '>已发送邮件<',
    r'>\s*Opened\s*<': '>HR 已阅读<',
    r'>\s*Replied\s*<': '>已收到回复<',
    r'>\s*Interview\s*<': '>获得面试邀请<',
}

files_translated = 0
for filename in os.listdir(zh_dir):
    if not filename.endswith('.html'):
        continue
    filepath = os.path.join(zh_dir, filename)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    for pattern, repl in UI_TRANSLATIONS.items():
        content = re.sub(pattern, repl, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    files_translated += 1

print(f"Applied complete UI translation to all {files_translated} Chinese templates!")
