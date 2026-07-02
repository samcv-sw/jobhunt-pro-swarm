import os

files = [
    "web/templates/contact.html",
    "web/templates/en/contact.html"
]

for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "System Logs" not in content and "/admin/sys-logs" not in content:
            # We insert it right before the WhatsApp floating button or after the WhatsApp card
            sys_log_html = """
                <!-- System Logs Card -->
                <a href="/admin/sys-logs" class="support-card" style="border-color:rgba(255,100,100,0.3);background:rgba(255,100,100,0.05)">
                    <div class="icon">??</div>
                    <h3>System Logs</h3>
                    <p>View server and error logs to quickly diagnose website issues. Admin only.</p>
                </a>
            """
            
            # Find the WhatsApp card closing tag and append sys_log_html
            import re
            content = re.sub(r'(<!-- WhatsApp Card -->.*?</a>)', r'\1' + sys_log_html, content, flags=re.DOTALL)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

print("System logs link added to contact pages.")
