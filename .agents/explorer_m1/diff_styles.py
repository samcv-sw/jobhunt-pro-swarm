import difflib
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def diff_files(file1, file2, name1, name2):
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        c1 = f1.read()
        c2 = f2.read()
    
    if c1 == c2:
        print(f"{name1} and {name2} are IDENTICAL!")
    else:
        print(f"{name1} and {name2} differ. Diff:")
        diff = difflib.unified_diff(c1.splitlines(), c2.splitlines(), fromfile=name1, tofile=name2)
        for line in diff:
            print(line)

print("--- style.css vs style-rtl.css ---")
diff_files(r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\style.css", 
           r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\style-rtl.css",
           "style.css", "style-rtl.css")

print("--- tailwind_overrides.css vs tailwind_overrides-rtl.css ---")
diff_files(r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\tailwind_overrides.css", 
           r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\tailwind_overrides-rtl.css",
           "tailwind_overrides.css", "tailwind_overrides-rtl.css")

print("--- index.css vs index-rtl.css ---")
diff_files(r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\index.css", 
           r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\index-rtl.css",
           "index.css", "index-rtl.css")
