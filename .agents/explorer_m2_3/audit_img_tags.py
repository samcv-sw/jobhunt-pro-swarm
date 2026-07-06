import os
import re

TEMPLATE_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

def main():
    missing_lazy = []
    
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if not file.endswith(".html"):
                continue
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            # Find all img tags
            img_tags = re.findall(r"<img[^>]*>", content, re.IGNORECASE)
            for tag in img_tags:
                if "loading=" not in tag.lower() or "lazy" not in tag.lower():
                    rel_path = os.path.relpath(path, TEMPLATE_DIR).replace("\\", "/")
                    missing_lazy.append((rel_path, tag))
                    
    print(f"Total img tags missing lazy loading: {len(missing_lazy)}")
    for rel_path, tag in missing_lazy:
        print(f"- {rel_path}: {tag}")

if __name__ == "__main__":
    main()
