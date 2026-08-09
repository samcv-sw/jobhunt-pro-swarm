import os
import shutil
import re

base_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"
zh_dir = os.path.join(base_dir, "zh")
en_dir = os.path.join(base_dir, "en")

os.makedirs(zh_dir, exist_ok=True)

# Step 1: Copy any missing .html files to zh_dir from base_dir or en_dir
base_htmls = [f for f in os.listdir(base_dir) if f.endswith(".html")]
for html_file in base_htmls:
    zh_path = os.path.join(zh_dir, html_file)
    if not os.path.exists(zh_path):
        src_path = os.path.join(en_dir, html_file) if os.path.exists(os.path.join(en_dir, html_file)) else os.path.join(base_dir, html_file)
        shutil.copy2(src_path, zh_path)
        print(f"Copied missing template: {html_file}")

# Step 2: Comprehensive dictionary of English & Arabic to Chinese translations
MASTER_DICT = {
    # HTML attributes & head
    r'lang="en"': 'lang="zh"',
    r'lang="ar"': 'lang="zh"',
    r'dir="rtl"': 'dir="ltr"',

    # Navigation & Links
    r'>\s*Home\s*<': '>首页<',
    r'>\s*Services\s*<': '>服务<',
    r'>\s*Pricing\s*<': '>价格<',
    r'>\s*Blog\s*<': '>博客<',
    r'>\s*FAQ\s*<': '>常见问题<',
    r'>\s*Trust\s*<': '>信任<',
    r'>\s*Contact\s*<': '>联系我们<',
    r'>\s*Contact Us\s*<': '>联系我们<',
    r'>\s*Dashboard\s*<': '>控制台<',
    r'>\s*Login\s*<': '>登录<',
    r'>\s*Log In\s*<': '>登录<',
    r'>\s*Log Out\s*<': '>退出登录<',
    r'>\s*Logout\s*<': '>退出登录<',
    r'>\s*Sign In\s*<': '>登录<',
    r'>\s*Sign Up\s*<': '>注册账号<',
    r'>\s*Register\s*<': '>注册账号<',
    r'>\s*Start Free →\s*<': '>免费开始 →<',
    r'>\s*Free Start →\s*<': '>免费开始 →<',
    r'>\s*Get Started Free\s*<': '>免费立即开始<',
    r'>\s*Get Started\s*<': '>立即开始<',

    # Sidebar & Dashboard Shell
    r'EMPLOYER &amp; TALENT SEARCH': '企业招聘与人才搜索',
    r'EMPLOYER & TALENT SEARCH': '企业招聘与人才搜索',
    r'Post a Job Opening': '发布招聘职位',
    r'Track Applicants \(ATS\)': '应聘者追踪 (ATS)',
    r'B2B Enterprise Portal': 'B2B 企业 Portal',
    r'B2B 企业尊享版 Portal': 'B2B 企业尊享版 Portal',
    r'Sent Emails': '已发送邮件记录',
    r'Premium Services': '高级精选服务',
    r'Special Offers': '限时优惠活动',
    r'My Subscriptions': '我的订阅与套餐',
    r'My Purchases': '我的已购项目',
    r'Wallet': '我的代币钱包',
    r'Stats': '系统数据统计',
    r'Growth Station': '增长中心',
    r'Referrals': '推荐返利计划',
    r'Email Test': '邮件测试工具',
    r'Export': '导出数据',
    r'API Docs': 'API 开发文档',
    r'System Logs': '系统运行日志',
    r'Notifications': '系统消息通知',
    r'Mark all read': '全部标记为已读',
    r'No notifications yet': '暂无新通知',
    r'Loading notifications\.\.\.': '正在加载通知...',

    # Dashboard Features & Sidebar Items
    r'0% Unemployment AI': '0% 失业 AI 智能体',
    r'AI Interview Copilot': 'AI 实时面试辅导',
    r'Salary Negotiator': '智能薪资谈判助手',
    r'ATS Resume Sculptor': 'ATS 简历优化器',
    r'ATS Scorer': 'ATS 简历评分',
    r'Resume Tailor': '简历定制工具',
    r'War Room': '求职作战指挥室',
    r'Battle Station': '全自动工作站',
    r'Auto Applier': '自动投递系统',
    r'Funnel Analytics': '漏斗数据分析',
    r'New Campaign': '新建求职计划',
    r'Upload CV': '上传个人简历',
    r'Settings': '账号设置',
    r'Overview': '数据概览',
    r'Active Campaigns': '运行中的求职计划',
    r'Recent Applications': '最新投递记录',
    r'Recommended Jobs': '推荐匹配职位',
    r'Application History': '历史投递列表',
    r'Status': '当前状态',
    r'Actions': '操作控制',
    r'View Details': '查看详情',
    r'View All': '查看全部',
    r'Export Data': '导出数据表',

    # Auth Pages (Login / Register / Reset Password)
    r'Welcome Back': '欢迎回来',
    r'Sign in to your JobHunt Pro account': '登录您的 JobHunt Pro 账号',
    r'Email Address': '电子邮箱地址',
    r'Enter your email': '请输入您的邮箱',
    r'Password': '密码',
    r'Enter your password': '请输入您的密码',
    r'Remember me': '记住我的登录',
    r'Forgot password\?': '忘记密码？',
    r'Forgot Password\?': '忘记密码？',
    r'Don\'t have an account\?': '还没有账号？',
    r'Already have an account\?': '已有账号？',
    r'Create your account': '创建您的 JobHunt Pro 账号',
    r'Full Name': '全名',
    r'Confirm Password': '确认密码',
    r'Reset Password': '重置密码',
    r'Send Reset Link': '发送重置邮件',
    r'Back to Login': '返回登录',

    # Badges & Status Terms
    r'>\s*Active\s*<': '>运行中<',
    r'>\s*Pending\s*<': '>处理中<',
    r'>\s*Completed\s*<': '>已完成<',
    r'>\s*Failed\s*<': '>失败<',
    r'>\s*Sent\s*<': '>已发件<',
    r'>\s*Opened\s*<': '>HR已读<',
    r'>\s*Replied\s*<': '>收到回复<',
    r'>\s*Interview\s*<': '>获得面试<',
    r'>\s*Applied\s*<': '>已投递<',

    # Common Landing Page & Marketing Blocks
    r'Autonomous AI Job Search Platform': '全自动 AI 智能求职平台',
    r'AI-Powered Job Application Engine': 'AI 驱动的自动化求职与投递引擎',
    r'Apply to thousands of jobs automatically': '全自动帮您投递数千个精选职位',
    r'Your personal job-hunting AI works 24/7': '您的专属求职 AI 智能体 24/7 全天候工作',
    r'Get hired faster': '助您快速拿到心仪 Offer',
    r'Built with ❤️ for job seekers worldwide\.': '用 ❤️ 为全球求职者打造。',
    r'All rights reserved\.': '保留所有权利。',
    r'Terms of Service': '服务条款',
    r'Privacy Policy': '隐私政策',
    r'Platform Comparison': '平台对比',
    r'Tech Support': '技术支持与客服',

    # Arabic Fallbacks to Chinese
    r'مرحباً بك في المنصة الذكية للتوظيف الجريء': '欢迎使用 JobHunt Pro 主权平台',
    r'لوحة التحكم الرئيسية والتحليلات الحية': '主控制台与实时分析',
    r'بدء التمرن على المقابلة بالذكاء الاصطناعي': '开始 AI 模拟面试',
    r'الوظائف الحصرية والأنظمة المباشرة': '隐藏 ATS 与未公开职位引擎',
    r'إعلان وظيفة': '职位列表',
    r'تقديم الآن': '立即申请',
    r'تصفية الوظائف': '筛选职位',
    r'لم يتم العثور على وظائف': '未找到匹配职位',
    r'تسجيل الدخول': '登录',
    r'إنشاء حساب': '注册账号',
    r'الرئيسية': '首页',
    r'الخدمات': '服务',
    r'الأسعار': '价格',
    r'المدونة': '博客',
    r'الأسئلة الشائعة': '常见问题',
    r'الثقة': '信任',
    r'غرفة القيادة': '控制台',
    r'تسجيل خروج': '退出登录',
    r'اتصل بنا': '联系我们',
    r'شروط الخدمة': '服务条款',
    r'سياسة الخصوصية': '隐私政策',
}

# Step 3: Run translations across all zh/ html files
updated_count = 0
for filename in os.listdir(zh_dir):
    if not filename.endswith(".html"):
        continue
    filepath = os.path.join(zh_dir, filename)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Ensure title and HTML lang attributes are zh
    content = re.sub(r'<html\s+lang=["\'][a-z]{2}["\']', '<html lang="zh"', content)
    content = re.sub(r'dir=["\']rtl["\']', 'dir="ltr"', content)

    for pattern, repl in MASTER_DICT.items():
        content = re.sub(pattern, repl, content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    updated_count += 1

print(f"Processed and updated {updated_count} files in web/templates/zh/")
