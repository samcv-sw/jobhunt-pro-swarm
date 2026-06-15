"""Strip DOCTYPE/head/body from standalone templates (convert to fragments)"""
import re

base = r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\templates'
files = ['new_campaign_v2.html', 'upload_cv_v2.html']

for fname in files:
    path = fr'{base}\{fname}'
    with open(path, 'rb') as f:
        data = f.read()
    text = data.decode('utf-8', errors='replace')
    
    print(f'{fname}: before={len(text)} chars')
    
    # Find the real content start (skip DOCTYPE, html, head sections)
    body_start = text.find('<body')
    if body_start >= 0:
        # Find the > that closes the <body> tag
        body_open_end = text.find('>', body_start) + 1
        content_start = body_open_end
        
        # Find </body> or </html>
        body_end_tag = text.find('</body>')
        html_end_tag = text.find('</html>')
        
        if body_end_tag >= 0:
            content_end = body_end_tag
        elif html_end_tag >= 0:
            content_end = html_end_tag
        else:
            content_end = len(text)
        
        # Extract just the inner content
        inner = text[content_start:content_end].strip()
        
        # Check if there's a <style> in the head that we should keep
        head_start = text.find('<style>')
        head_end = text.find('</style>')
        extra_styles = ''
        if head_start >= 0 and head_end > head_start and (head_start < body_start):
            # Extract style from head
            style_content = text[head_start + 7:head_end]
            if '<link rel="stylesheet"' not in inner and len(style_content) > 100:
                # Add the style block before content if it's not already in the body
                extra_styles = f'<style>{style_content}</style>\n'
        
        # Don't strip cyberpunk.css link from head - keep it as it's needed
        # But DO strip the DOCTYPE, html, head wrapper
        # Check if cyberpunk.css is already referenced
        has_cyber = 'cyberpunk.css' in inner
        
        new_text = extra_styles + inner
        
        # Also need to import cyberpunk.css if not present
        if not has_cyber and 'cyberpunk.css' not in new_text:
            new_text = f'<link rel="stylesheet" href="/static/css/cyberpunk.css">\n{new_text}'
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        
        print(f' after={len(new_text)} chars (stripped wrapper)')
        print(f' first 100: {new_text[:100]}')
    else:
        print(f' NO body tag found (already fragment?)')
        print(f' first 100: {text[:100]}')
