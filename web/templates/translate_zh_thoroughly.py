import os
import re

zh_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\zh"

# Full replacement dictionary for every single remaining English block
THOROUGH_REPLACEMENTS = {
    # Typewriter JS
    r"words=\['Sleep','Relax','Live Your Life','Focus on Interviews','Earn More','Thrive'\];": "words=['轻松休息','享受生活','专注面试','提高薪资','快速入职','成就事业'];",
    
    # Process & Steps
    r'THE PROCESS': '运作流程',
    r'How It <span class="gradient">Works</span>': '全自动 <span class="gradient">求职流程</span>',
    r'Four simple steps from uploading your resume to landing interviews\. Zero manual work required\.': '从上传简历到获得面试邀请仅需 4 步，全程无需人工干预。',
    r'Upload Your CV': '上传您的简历',
    r'Drop your PDF or paste your CV text\. Our AI instantly extracts your skills, experience, education, and career preferences\.': '拖拽 PDF/Word 简历或粘贴文本，AI 智能提取并分析您的核心工作经验与技能亮点。',
    r'Set Your Target': '设定求职目标',
    r'Choose job titles, locations, and salary range\. We search across multiple engines in all 195\+ countries worldwide worldwide\.': '设置目标职位、意向城市及期望薪资，AI 将在全球主流招聘平台全网搜索。',
    r'AI Does The Work': 'AI 智能集群执行',
    r'Hundreds of AI agents craft unique cover letters for each company and send through smart email rotation\. Zero spam flags\.': '数百个 AI 智能体为每个岗位撰写专属求职信，通过智能邮箱轮换投递，确保高送达率。',
    r'Get Interviews': '收获面试邀请',
    r'Track opens, clicks, and responses in real-time\. Automatic follow-ups ensure maximum response rates\. Land the job\.': '实时追踪邮件打开率与回复，自动发送跟进邮件，最大化提高面试转化率。',

    # Before vs After Comparison
    r'⚡ THE TRANSFORMATIONAL DIFFERENCE': '⚡ 颠覆性的求职体验差异',
    r'Job Search: <span class="gradient">Before vs After</span>': '求职对比：<span class="gradient">传统手动 vs AI 自动化</span>',
    r'What your job hunt looks like with manual searching versus JobHunt Pro automation': '对比手动检索投递与 JobHunt Pro 全自动智能求职的效率差异',
    r'Traditional Manual Job Search': '传统手动求职方式',
    r'40\+ hours/week manually scrolling job boards': '每周耗费 40+ 小时人工浏览招聘网站',
    r'Copy-pasting the same generic cover letter': '复制粘贴通用的求职信，缺乏针对性',
    r'Missing 80% of newly posted high-salary roles': '错失 80% 最新发布的优质高薪职位',
    r'Emails constantly landing in recipient spam folders': '发件容易进入 HR 垃圾邮件箱',
    r'Zero tracking or visibility into sent applications': '投递后缺乏数据追踪与反馈',
    r'2-3% interview rate on average globally': '平均面试邀请率仅为 2%-3%',
    r'Extreme burnout and frustration within 3 weeks': '连续几周无回应导致求职焦虑与疲惫',
    r'VS': '对比',
    r'⚡ THE CHOICE IS CLEAR': '⚡ 结果显而易见',
    r'JobHunt Pro Autonomous AI': 'JobHunt Pro AI 全自动求职',
    r'0 hours/week spent — 100% fully automated': '0 小时/周 — 100% 全自动无人值守',
    r'AI generates custom tailored cover letters per role': 'AI 为每个岗位生成专属求职信',
    r'Catches and applies to every new job opening instantly': '实时捕获最新职位发布并第一时间投递',
    r'20\+ rotating provider mesh = 99% inbox placement': '多通道邮箱轮换 = 99% 直接送达 HR 收件箱',
    r'Live real-time analytical dashboard tracks everything': '实时数据控制台追踪全流程状态',
    r'8-15% interview rate \(4x higher response rate\)': '面试邀请率达 8%-15%（提升 4 倍以上）',
    r'Sustainable — operates 24/7 autonomously while you sleep': '全天候 24/7 自动运行，休息时也在投递',

    # Features
    r'PLATFORM FEATURES': '平台核心功能',
    r'Everything You <span class="gradient">Need</span>': '助您成功入职的 <span class="gradient">全套 AI 工具</span>',
    r'A complete job application arsenal — every tool you need to automate your entire job search, built right in\.': '一站式自动化求职套件 — 涵盖全自动投递、简历优化及面试辅导全流程。',
    r'AI-Powered Personalization': 'AI 深度个性化定制',
    r'Advanced AI crafts unique, personalized cover letters for every single company\. Reads the job description, understands requirements, and tailors perfectly — never generic, never templated\.': '高阶 AI 深入解析每个职位要求，生成专属求职信，绝非通用模板。',
    r'Multi-Provider Email System': '多通道邮箱轮换系统',
    r'Smart rotation across Graham\'s Infinite Provider Rotation Mesh with intelligent warmup, spam-score checking, and automatic fallback\. Your applications always land in the inbox, never in spam\.': '智能轮换 dedicated SMTP 发信通道，确保邮件安全直接进 HR 收件箱。',
    r'Multi-Engine Job Search': '全网多引擎求职搜索',
    r'We search across all major platforms — every job board, every company career page, every listing worldwide\. all 195\+ countries worldwide, all industries, all levels\.': '覆盖全球各大招聘平台与企业官网，支持 195+ 国家与地区及全行业岗位。',
    r'Stealth Protection': '反追踪安全防护',
    r'Smart delays, human-like timing patterns, and sophisticated anti-detection\. Email providers never flag you\. Sophisticated algorithms keep you completely under the radar\.': '模拟人类行为模式与智能延迟投递，保护发件邮箱声誉，安全稳定。',
    r'Automatic Follow-Ups': '自动定时跟进邮件',
    r'If no response, our system automatically sends polite, personalized follow-up emails\. Boosts response rates by up to 40%\. Never miss an opportunity because you forgot to follow up\.': '若超时未收到回复，系统自动发送礼貌跟进邮件，提升 40% 回复率。',

    # ATS Checker
    r'🔍 ATS RESUME CHECKER': '🔍 ATS 简历匹配度检测',
    r'Is Your Resume <span class="gradient">ATS-Ready\?</span>': '您的简历通过 <span class="gradient">ATS 筛选了吗？</span>',
    r'99% of Fortune 500 companies use ATS\. JobHunt Pro scans your resume against real job descriptions and shows exactly what to fix — <strong style="color:var\(--cyan\)">free</strong>\.': '99% 的知名企业使用 ATS 筛选简历。JobHunt Pro 帮助您检测并优化简历关键词。',
    r'Drag your resume here or click to upload': '拖拽简历至此处或点击上传',
    r'Supported formats: PDF, DOCX, TXT \(Max 10MB\)': '支持格式：PDF, DOCX, TXT (最大 10MB)',

    # Featured Jobs Section
    r'HOT OPPORTUNITIES': '热门精选职位',
    r'Featured <span class="gradient">Jobs</span>': '最新精选 <span class="gradient">职位推荐</span>',
    r'Hand-picked premium positions in top companies across MENA/GCC\. Apply instantly with JobHunt Pro\.': '为您精选知名企业的优质岗位，一键通过 JobHunt Pro 自动投递。',
    r'★ Featured': '★ 精选推荐',
}

files_updated = 0
for filename in os.listdir(zh_dir):
    if not filename.endswith('.html'):
        continue
    filepath = os.path.join(zh_dir, filename)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    for pattern, repl in THOROUGH_REPLACEMENTS.items():
        content = re.sub(pattern, repl, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    files_updated += 1

print(f"Applied thorough replacements to {files_updated} templates in web/templates/zh/")
