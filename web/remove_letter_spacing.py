import os
import re

def remove_letter_spacing(directory):
    count = 0
    pattern = re.compile(r'letter-spacing\s*:\s*[^;]+;?')
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith('.css') or f.endswith('.html'):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    new_content, num_subs = pattern.subn('', content)
                    
                    if num_subs > 0:
                        with open(path, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        print(f"Removed {num_subs} letter-spacing from {path}")
                        count += 1
                except Exception as e:
                    print(f"Error processing {path}: {e}")
    print(f"Done. Modified {count} files.")

if __name__ == "__main__":
    remove_letter_spacing('C:\\Users\\samde\\Desktop\\📂 Folders & Projects\\cv sam new ma3 kimi\\web')
