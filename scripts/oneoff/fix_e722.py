import glob
import os
import re

# Files to process
files = []
files.extend(glob.glob("core/**/*.py", recursive=True))
files.extend(glob.glob("web/**/*.py", recursive=True))

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace 'except:' with 'except Exception:'
    # Make sure we match 'except:' with optional whitespace before the colon
    # and we only match it if it's not part of something else (using word boundary)
    new_content = re.sub(r'\bexcept\s*:', 'except Exception:', content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed bare excepts in {filepath}")
