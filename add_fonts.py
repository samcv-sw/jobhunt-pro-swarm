import os

files_to_process = [
    r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\index_v2.html",
    r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\index_v3.html"
]

cairo_link = '<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800;900&family=IBM+Plex+Arabic:wght@300;400;500;600;700&family=Tajawal:wght@300;400;500;700;800;900&display=swap" rel="stylesheet">'
text_dir_var = "   --text-x-direction: -1;\n"

def update_fonts(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add Google Fonts link
    if "family=Cairo" not in content:
        content = content.replace('<!-- Fonts -->', f'<!-- Fonts -->\n {cairo_link}')
        content = content.replace('<link href="https://fonts.googleapis.com/css2?family=Inter', f'{cairo_link}\n <link href="https://fonts.googleapis.com/css2?family=Inter')
        
    # Add text-x-direction variable
    if "--text-x-direction" not in content:
        content = content.replace(':root{', f':root{{\n{text_dir_var}')
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for fp in files_to_process:
    update_fonts(fp)
