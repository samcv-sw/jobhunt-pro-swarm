import os, re

def fix_centering_in_dir(directory):
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".html") or f.endswith(".css"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                
                # Replace inset-inline-start: 50% -> left: 50%
                new_content = re.sub(r"inset-inline-start:\s*50%", "left: 50%", content)
                
                # Let's also check if there's inset-inline-end: 50% just in case
                new_content = re.sub(r"inset-inline-end:\s*50%", "right: 50%", new_content)
                
                # If there's transform:translateX(50%) that was meant to be physical, it will now match left:50%.
                
                if new_content != content:
                    with open(path, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    print(f"Fixed centering in {path}")

fix_centering_in_dir("templates")
fix_centering_in_dir("static")
print("Done fixing centering")
