import os
import re

zh_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\zh"

# Comprehensive dictionary for translating English landing/dashboard templates to Chinese
FULL_ZH_DICTIONARY = {
    # Hero Section & Titles
    r'Land Your Dream Job\s*<br>\s*<span class="cyan glow-line">Automatically</span>\s*While You\s*<br>': '轻松拿到心仪 Offer<br><span class="cyan glow-line">全自动 AI 求职投递</span> 助您高效升职<br>',
    r'Land Your Dream Job Automatically While You': '轻松拿到心仪 Offer — 全自动 AI 求职投递',
    r'Your personal AI job-hunting engine works <strong style="color:var\(--cyan\)">24/7</strong> — searching thousands of jobs,\s*crafting personalized applications, and sending them through smart email rotation\.': '专属 AI 智能求职引擎 <strong style="color:var(--cyan)">24/7</strong> 全天候运行 — 自动搜索数千个职位、精准雕琢个性化简历求职信、并通过智能邮箱轮换高效投递。',
    r'Get hired or your money back\.': '助您快速入职，不成功全额退款。',
    r'🚀 Start Applying Now — It\'s Free': '🚀 立即免费开始投递',
    r'💰 View Pricing Plans': '💰 查看套餐价格',
    r'>\s*Daily Applications\s*<': '>每日自动投递<',
    r'>\s*Email Providers\s*<': '>邮箱轮换通道<',
    r'>\s*AI Agents\s*<': '>AI 智能智能体<',
    r'>\s*Countries\s*<': '>覆盖国家与地区<',
    r'>\s*Interview Rate\s*<': '>面试邀请率<',
    
    # Guarantee & Platform Bar
    r'30-Day Money-Back Guarantee': '30 天全额退款保障',
    r'Zero interview invites in 30 days\? Get a full 100% refund — no questions asked\. Your risk is ZERO\.': '30 天内若未收到面试邀请，全额 100% 退款 — 无需任何理由，真正零风险。',
    r'SEARCHING ACROSS THESE PLATFORMS \+ MORE': '覆盖全球及中东主流招聘平台与搜索引擎',
    
    # How It Works
    r'HOW IT WORKS': '运作流程',
    r'4 Steps to Your New Job': '只需 4 步，轻松入职新岗位',
    r'From setup to interview invitations in minutes': '从完成设置到收到面试邀请，仅需几分钟',
    r'Step 1': '第 1 步',
    r'Upload CV': '上传简历',
    r'Upload your resume in PDF/Word format\. Our AI analyzes your experience, skills, and achievements\.': '上传 PDF 或 Word 格式简历，AI 智能提取并分析您的核心工作经验与技能亮点。',
    r'Step 2': '第 2 步',
    r'Set Preferences': '设置求职意向',
    r'Define target job titles, preferred locations, target salary range, and remote/onsite options\.': '自定义目标职位、期望工作地点、目标薪资范围以及远程/现场办公偏好。',
    r'Step 3': '第 3 步',
    r'AI Swarm Activates': 'AI 智能集群启动',
    r'200\+ AI agents scan top job portals, score matches, write custom cover letters, and auto-submit\.': '200+ AI 智能体全天候检索各大招聘网站，精准匹配职位、撰写专属求职信并自动投递。',
    r'Step 4': '第 4 步',
    r'Receive Interviews': '接收面试邀请',
    r'Check your dashboard to track live applications and start receiving direct interview invites from recruiters\.': '登录控制台随时查看投递状态，轻松接收 HR 和招聘经理发来的面试邀请。',
    
    # Features
    r'SOVEREIGN FEATURES': '核心强悍功能',
    r'Why JobHunt Pro Outperforms Everything Else': '为什么 JobHunt Pro 比传统求职方式更高效',
    r'Engineered for maximum interview throughput': '专为提升面试转化率与求职效率而设计',
    r'Autonomous Auto-Applier': '全自动求职投递',
    r'Applies to hundreds of verified jobs daily without human intervention\.': '每日自动匹配并投递数百个验证真实的优质职位，无需人工繁琐操作。',
    r'ATS Match Score Optimizer': 'ATS 简历匹配度优化',
    r'Scores your CV against job descriptions and injects missing keywords to bypass recruiter screeners\.': '实时对比职位要求打分，智能补充关键词，助您轻松通过 ATS 筛选系统。',
    r'AI Cover Letter Engine': 'AI 专属求职信生成器',
    r'Generates hyper-personalized, ultra-converting cover letters tailored specifically for each role\.': '为每一个职位量身定制高吸引力的专属 Cover Letter，极大提升 HR 回复率。',
    r'Smart Email Rotation': '智能多邮箱轮换发件',
    r'Distributes sending across dedicated SMTP pools to maintain strict domain reputation and bypass spam filters\.': '使用多通道 dedicated SMTP 邮箱轮换投递，确保求职邮件直接进入 HR 邮箱。',
    r'Live Interview Copilot': '实时 AI 面试助手',
    r'Real-time voice and text suggestions during your actual interviews to help you answer tough questions\.': '面试过程中提供实时语音与文本建议，助您从容应对各类高难度技术与行为面试题。',
    r'AI Salary Negotiator': '智能薪资谈判策略',
    r'Market analytics and AI-crafted counter-offers that help you secure 15-30% higher starting packages\.': '基于业内权威数据与 AI 谈判话术，助您在薪资谈判中获得 15%-30% 的薪酬提升。',
    
    # Pricing
    r'PRICING PLANS': '套餐价格',
    r'Invest in Your Career Acceleration': '选择最适合您的职业加速方案',
    r'Simple, transparent pricing\. No hidden fees\. Cancel anytime\.': '价格透明清晰，无任何隐藏费用，随时可取消订阅。',
    r'Starter': '基础版',
    r'Professional': '专业版',
    r'Enterprise': '企业尊享版',
    r'/month': '/月',
    r'MOST POPULAR': '最受欢迎',
    r'Get Started Now': '立即开始使用',
    r'Choose Plan': '选择此套餐',

    # Auth & Forms
    r'Welcome Back': '欢迎回来',
    r'Log in to your account': '登录您的账号以继续',
    r'Email Address': '电子邮箱地址',
    r'Enter your email': '请输入电子邮箱',
    r'Password': '密码',
    r'Enter your password': '请输入密码',
    r'Forgot Password\?': '忘记密码？',
    r'Remember me': '记住登录状态',
    r'Sign In to Dashboard': '登录控制台',
    r'Don\'t have an account\? Register': '还没有账号？立即注册',
    r'Already have an account\? Login': '已有账号？立即登录',
    r'Create Your Account': '创建您的求职账号',
    r'Full Name': '真实姓名',
    r'Enter your full name': '请输入您的姓名',
    r'Confirm Password': '确认密码',
    r'Re-enter your password': '请再次输入密码',
    r'I agree to the Terms of Service and Privacy Policy': '我已阅读并同意服务条款与隐私政策',
    r'Create Account &amp; Start Free': '注册账号并免费试用',
    r'Create Account & Start Free': '注册账号并免费试用',

    # Footer
    r'All rights reserved\.': '保留所有权利。',
    r'Privacy Policy': '隐私政策',
    r'Terms of Service': '服务条款',
    r'Security &amp; Trust': '安全与信任',
    r'Security & Trust': '安全与信任',
    r'System Status': '系统运行状态',
    r'All Systems Operational': '所有系统正常运行中',
}

files_translated = 0
for filename in os.listdir(zh_dir):
    if not filename.endswith('.html'):
        continue
    filepath = os.path.join(zh_dir, filename)
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Apply all comprehensive Chinese replacements
    for pattern, repl in FULL_ZH_DICTIONARY.items():
        content = re.sub(pattern, repl, content)

    # Ensure root HTML tag has lang="zh" and dir="ltr"
    content = re.sub(r'<html[^>]*>', '<html lang="zh" dir="ltr">', content, count=1)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    files_translated += 1

print(f"Comprehensive Chinese translation applied to {files_translated} templates in web/templates/zh/")
