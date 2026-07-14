
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\new_campaign_v2.html'
with open(file_path, encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Launch Campaign': 'إطلاق حملة جديدة',
    'Deploy an autonomous AI swarm to hunt and apply for jobs on your behalf.': 'انشر فريقاً من الذكاء الاصطناعي للبحث والتقديم للوظائف نيابة عنك.',
    'You need to add funds to your wallet before deploying a campaign.': 'يجب إضافة رصيد إلى محفظتك قبل إطلاق حملة.',
    'Select CV Profile': 'اختر السيرة الذاتية',
    'Delete selected profile': 'حذف السيرة الذاتية المحددة',
    'Select 1': 'اختر واحدة',
    '''Optional add-ons to boost your campaign's success rate.''': 'إضافات اختيارية لزيادة نسبة نجاح حملتك.',
    'Start Autonomous Campaign': 'إطلاق حملة البحث الذاتي',
    'Estimated Cost:': 'التكلفة التقديرية:',
    'Wallet Balance:': 'رصيد المحفظة:'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

logger.info('new_campaign_v2.html translated successfully.')
