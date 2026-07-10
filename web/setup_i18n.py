import os
import shutil
import subprocess

base_dir = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"
ar_dir = os.path.join(base_dir, "ar")
en_dir = os.path.join(base_dir, "en")

os.makedirs(ar_dir, exist_ok=True)
os.makedirs(en_dir, exist_ok=True)

logger.debug("Moving current files to ar/")
for f in os.listdir(base_dir):
    src = os.path.join(base_dir, f)
    if os.path.isfile(src) and (f.endswith('.html') or f.endswith('.py')):
        shutil.move(src, os.path.join(ar_dir, f))

logger.debug("Extracting English files from commit fff5024...")
# We use git ls-tree to list files in fff5024:web/templates
cwd = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web"
result = subprocess.run(["git", "ls-tree", "--name-only", "fff5024", "templates"], cwd=cwd, capture_output=True, text=True)
files = result.stdout.strip().split('\n')

for f in files:
    f = f.strip()
    if not f: continue
    filename = os.path.basename(f)
    if filename.endswith('.html') or filename.endswith('.py'):
        # Get content
        try:
            content = subprocess.run(["git", "show", f"fff5024:web/{f}"], cwd=cwd, capture_output=True).stdout
            with open(os.path.join(en_dir, filename), "wb") as out:
                out.write(content)
        except Exception as e:
            logger.debug(f"Failed to extract {filename}: {e}")

logger.debug("Done setting up directories.")
