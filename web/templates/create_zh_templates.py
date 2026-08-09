import os
import re

en_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\en"
root_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"
zh_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\zh"

os.makedirs(zh_dir, exist_ok=True)

# Extended Translation Dictionary mapping English/Arabic phrases to Simplified Chinese
REPLACEMENTS = {
    # Layout & Language tags
    r'lang="en"': 'lang="zh"',
    r"lang='en'": "lang='zh'",
    r'lang="ar"': 'lang="zh"',
    r"lang='ar'": "lang='zh'",
    r'hreflang="en"': 'hreflang="zh"',
    r'en/_public_nav\.html': 'zh/_public_nav.html',
    r'en/_public_footer\.html': 'zh/_public_footer.html',
    r'en/_public_shell\.html': 'zh/_public_shell.html',
    r'en/_sidebar\.html': 'zh/_sidebar.html',
    r'en/_dashboard_shell\.html': 'zh/_dashboard_shell.html',
    r'ar/_public_nav\.html': 'zh/_public_nav.html',
    r'ar/_public_footer\.html': 'zh/_public_footer.html',

    # Navigation & Core Buttons
    r'>\s*Home\s*<': '>首页<',
    r'>\s*Services\s*<': '>服务<',
    r'>\s*Pricing\s*<': '>价格<',
    r'>\s*Blog\s*<': '>博客<',
    r'>\s*FAQ\s*<': '>常见问题<',
    r'>\s*Trust\s*<': '>信任<',
    r'>\s*Contact Us\s*<': '>联系我们<',
    r'>\s*Contact\s*<': '>联系我们<',
    r'>\s*Dashboard\s*<': '>控制台<',
    r'>\s*Login\s*<': '>登录<',
    r'>\s*Log Out\s*<': '>退出登录<',
    r'>\s*Start Free\s*→\s*<': '>免费开始 →<',
    r'>\s*Get Started Free\s*<': '>免费开始体验<',
    r'>\s*Sign In\s*<': '>登录账号<',
    r'>\s*Register\s*<': '>注册账号<',
    r'>\s*Create Account\s*<': '>创建新账号<',
    r'>\s*Save\s*<': '>保存<',
    r'>\s*Cancel\s*<': '>取消<',
    r'>\s*Submit\s*<': '>提交<',
    r'>\s*Delete\s*<': '>删除<',
    r'>\s*Edit\s*<': '>编辑<',
    r'>\s*Update\s*<': '>更新<',
    r'>\s*Close\s*<': '>关闭<',
    r'>\s*Upload\s*<': '>上传<',
    r'>\s*Download\s*<': '>下载<',
    r'>\s*Search\s*<': '>搜索<',
    r'>\s*Add\s*<': '>添加<',
    r'>\s*Create\s*<': '>创建<',
    r'>\s*Next\s*<': '>下一步<',
    r'>\s*Previous\s*<': '>上一步<',
    r'>\s*Back\s*<': '>返回<',
    r'>\s*Settings\s*<': '>设置<',
    r'>\s*Overview\s*<': '>概览<',
    r'>\s*Analytics\s*<': '>数据分析<',
    r'>\s*Features\s*<': '>核心功能<',

    # Arabic Fallbacks
    r'>\s*الرئيسية\s*<': '>首页<',
    r'>\s*الخدمات\s*<': '>服务<',
    r'>\s*الأسعار\s*<': '>价格<',
    r'>\s*المدونة\s*<': '>博客<',
    r'>\s*الأسئلة الشائعة\s*<': '>常见问题<',
    r'>\s*اتصل بنا\s*<': '>联系我们<',
    r'>\s*تسجيل الدخول\s*<': '>登录<',
    r'>\s*إنشاء حساب\s*<': '>注册<',
    r'>\s*غرفة القيادة\s*<': '>控制台<',
    r'>\s*لوحة التحكم\s*<': '>控制台<',
    r'>\s*تسجيل خروج\s*<': '>退出登录<',
    r'>\s*حفظ\s*<': '>保存<',
    r'>\s*إلغاء\s*<': '>取消<',
    r'>\s*إرسال\s*<': '>提交<',

    # Landing Page & Headlines
    r'JobHunt Pro &#x2014; AI-Powered Automated Job Applications': 'JobHunt Pro — AI 智能自动求职与投递平台',
    r'JobHunt Pro — AI-Powered Automated Job Applications': 'JobHunt Pro — AI 智能自动求职与投递平台',
    r'AI-Powered Job Application Engine': 'AI 智能自动求职与投递引擎',
    r'Apply to thousands of jobs automatically\.': '自动投递数千个职位，让 AI 智能为您全天候寻找工作。',
    r'Your personal job-hunting AI works 24/7\.': '您的专属 AI 求职助手 24/7 全天候运行。',
    r'Get hired faster\.': '快速获得理想工作。',
    r'Less than 7 cents per application\.': '平均每次投递成本低于 7 美分。',
    r'Autonomous Auto-Applier': '自动投递集群',
    r'ATS Resume Analyzer': 'ATS 简历匹配分析器',
    r'ATS Resume Sculptor': 'ATS 简历雕刻分析器',
    r'Live Interview Copilot': '实时面试 AI 助手',
    r'AI Salary Negotiator': '智能薪资谈判助手',
    r'Sovereign Dashboard': '主控指挥中心',
    r'Command Center': '指挥中心',
    r'Total Applications': '总投递职位数',
    r'Success Rate': '投递成功率',
    r'Response Rate': '面试回复率',
    r'Active &amp; Running': '全天候运行中',
    r'Active & Running': '全天候运行中',
    r'Apply Now': '立即申请',
    r'Post a New Job Opening': '发布新职位招聘',
    r'Post Your Job': '发布招聘职位',
    r'Why JobHunt Pro\?': '为什么选择 JobHunt Pro？',
    r'Employers': '企业雇主',
    r'Upload CV &amp; Profiles': '上传简历与个人资料',
    r'Upload CV & Profiles': '上传简历与个人资料',
    r'Email Address': '电子邮箱地址',
    r'Password': '密码',
    r'Forgot Password\?': '忘记密码？',
    r'Remember me': '记住我',
    r"Don't have an account\?": '还没有账号？',
    r'Already have an account\?': '已有账号？',
    r'How It Works': '工作原理',
    r'Frequently Asked Questions': '常见问题解答',
    r'Everything You Need': '您需要的一切功能',
    r'Choose Your Plan': '选择您的订阅方案',
    r'What Our Users Say': '用户真实评价',
    r'Featured Jobs': '热门精选职位',
    r'All Rights Reserved': '保留所有权利',
    r'Privacy Policy': '隐私政策',
    r'Terms of Service': '服务条款',
    r'Wait! Before you go\.\.\.': '等等！在您离开之前...',
    r'Ready to Win Your Job Search\?': '准备好赢取您的理想工作了吗？',
    r'See The Dashboard In Action': '亲自体验控制台',
    r'Bulk Job Packages': '批量职位套餐',
    r'Power-Ups': '高级功能扩展',
    r'User Info': '用户信息',
    r'Campaigns': '投递活动',
    r'Sent Emails': '已发邮件',
    r'Full Name': '姓名',
    r'Phone Number': '手机号码',
    r'Location': '工作地点',
    r'Job Title': '职位名称',
    r'Company': '公司',
    r'Status': '状态',
    r'Date': '日期',
    r'Actions': '操作',
}

def process_file(src_path, dst_path):
    with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Apply regex replacements
    for pattern, repl in REPLACEMENTS.items():
        content = re.sub(pattern, repl, content)

    # Force lang="zh" and dir="ltr"
    content = re.sub(r'<html[^>]*>', '<html lang="zh" dir="ltr">', content, count=1)

    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(content)

files_processed = 0

# 1. Process all files in web/templates/en/
for filename in os.listdir(en_dir):
    if filename.endswith('.html'):
        src_path = os.path.join(en_dir, filename)
        dst_path = os.path.join(zh_dir, filename)
        process_file(src_path, dst_path)
        files_processed += 1

# 2. Also process any html files in web/templates/ root if missing from en_dir
for filename in os.listdir(root_dir):
    if filename.endswith('.html'):
        dst_path = os.path.join(zh_dir, filename)
        if not os.path.exists(dst_path):
            src_path = os.path.join(root_dir, filename)
            process_file(src_path, dst_path)
            files_processed += 1

print(f"Successfully generated/updated {files_processed} Chinese templates in web/templates/zh/")
