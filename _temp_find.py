with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('.bs-card{')
print(f'Found .bs-card at index: {idx}')
print(repr(content[idx:idx+80]))
idx2 = content.find('content = f\'\'\'<style>\n.bs-card')
print(f'Found content start at: {idx2}')
if idx2 > 0:
    print(repr(content[idx2:idx2+60]))
