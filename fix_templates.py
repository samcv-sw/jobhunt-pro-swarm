import os
import glob
import re

template_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

for fpath in glob.glob(os.path.join(template_dir, "**", "register*.html"), recursive=True):
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # We want to replace the `cf-turnstile` div if it has the default dummy key.
    # The current markup might look like:
    # <div class="turnstile-wrap">
    #   <div class="cf-turnstile" data-sitekey="{{ turnstile_site_key | default('1x00000000000000000000AA', true) }}" data-theme="dark"></div>
    # </div>
    
    # Let's replace the whole turnstile-wrap logic
    pattern = r'<div class="turnstile-wrap">.*?<div class="cf-turnstile" data-sitekey="\{\{ turnstile_site_key.*?</div>.*?</div>'
    
    replacement = """{% if turnstile_site_key %}
      <div class="turnstile-wrap">
        <div class="cf-turnstile" data-sitekey="{{ turnstile_site_key }}" data-theme="dark"></div>
      </div>
      {% endif %}"""
      
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Patched {fpath}")
