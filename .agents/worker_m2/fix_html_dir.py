import os
import re

dir_path = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\en"

for filename in os.listdir(dir_path):
    if filename.endswith(".html"):
        file_path = os.path.join(dir_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Regex to match <html ...>
        # We want to insert dir="ltr" if it's not already there.
        match = re.search(r'<html([^>]*)>', content, re.IGNORECASE)
        if match:
            attrs = match.group(1)
            if 'dir=' not in attrs.lower():
                # Add dir="ltr" to the attributes
                new_attrs = f' dir="ltr"{attrs}'
                new_tag = f'<html{new_attrs}>'
                new_content = content.replace(match.group(0), new_tag)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {filename}: added dir=\"ltr\"")
