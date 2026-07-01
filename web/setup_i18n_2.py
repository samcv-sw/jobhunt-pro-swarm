import os
import shutil
import subprocess

repo_dir = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi"
tpl_dir = os.path.join(repo_dir, "web", "templates")
en_dir = os.path.join(tpl_dir, "en")

print("Checking out fff5024 web/templates...")
subprocess.run(["git", "checkout", "fff5024", "--", "web/templates"], cwd=repo_dir)

print("Moving files to en/...")
for f in os.listdir(tpl_dir):
    src = os.path.join(tpl_dir, f)
    if os.path.isfile(src) and (f.endswith('.html') or f.endswith('.py')):
        shutil.move(src, os.path.join(en_dir, f))

print("Unstaging changes...")
subprocess.run(["git", "reset", "HEAD", "web/templates"], cwd=repo_dir)

print("Done.")
