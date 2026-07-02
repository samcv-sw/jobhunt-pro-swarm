import os

files = [
    "web/templates/dashboard_v3.html",
    "web/templates/en/dashboard_v3.html"
]

modal_html = """
<!-- SMTP Connect Modal -->
<dialog id="smtpModal" class="modal rounded-xl border border-white/10 bg-slate-900/95 p-6 backdrop-blur-xl text-white shadow-2xl" style="width: 100%; max-width: 450px;">
  <div class="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
    <h3 class="text-xl font-bold text-white">Connect Your Email</h3>
    <button onclick="document.getElementById('smtpModal').close()" class="text-slate-400 hover:text-white"><i data-lucide="x" class="h-5 w-5"></i></button>
  </div>
  <p class="text-sm text-slate-400 mb-6">Send job applications directly from your own email address to bypass spam filters and increase response rates.</p>
  
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Provider</label>
      <select id="smtpProvider" class="w-full rounded-lg border border-white/10 bg-slate-800 p-2.5 text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500">
        <option value="google">Google (Gmail/Workspace)</option>
        <option value="microsoft">Microsoft (Outlook/Office365)</option>
      </select>
    </div>
    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Email Address</label>
      <input type="email" id="smtpEmail" placeholder="you@domain.com" class="w-full rounded-lg border border-white/10 bg-slate-800 p-2.5 text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500">
    </div>
    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">App Password</label>
      <input type="password" id="smtpPass" placeholder="16-digit App Password" class="w-full rounded-lg border border-white/10 bg-slate-800 p-2.5 text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500">
      <p class="text-xs text-slate-500 mt-1"><a href="https://support.google.com/accounts/answer/185833" target="_blank" class="text-indigo-400 hover:underline">How to generate an App Password?</a></p>
    </div>
    <button id="smtpConnectBtn" onclick="connectSmtp()" class="w-full rounded-lg bg-indigo-600 py-3 font-bold text-white transition-all hover:bg-indigo-500 mt-4 flex justify-center items-center gap-2">
      <i data-lucide="link" class="h-4 w-4"></i> Connect Securely
    </button>
  </div>
</dialog>

<script>
async function connectSmtp() {
    const provider = document.getElementById('smtpProvider').value;
    const email = document.getElementById('smtpEmail').value;
    const pass = document.getElementById('smtpPass').value;
    
    if(!email || !pass) {
        alert('Please enter both email and app password.');
        return;
    }
    
    const btn = document.getElementById('smtpConnectBtn');
    btn.innerHTML = '<i class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></i> Connecting...';
    btn.disabled = true;
    
    try {
        const res = await fetch('/api/smtp-connect', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({provider, email, app_password: pass})
        });
        const data = await res.json();
        if(res.ok) {
            alert(data.message);
            window.location.reload();
        } else {
            alert(data.message || 'Error connecting.');
            btn.innerHTML = '<i data-lucide="link" class="h-4 w-4"></i> Connect Securely';
            btn.disabled = false;
        }
    } catch(e) {
        alert('Network error.');
        btn.innerHTML = '<i data-lucide="link" class="h-4 w-4"></i> Connect Securely';
        btn.disabled = false;
    }
}
</script>
"""

for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "id=\"smtpModal\"" not in content:
            # Replace the hrefs in the banner to trigger the modal instead of oauth login
            content = content.replace('href="/oauth/microsoft/login"', 'onclick="document.getElementById(\'smtpModal\').showModal(); document.getElementById(\'smtpProvider\').value=\'microsoft\'"')
            content = content.replace('href="/oauth/google/login"', 'onclick="document.getElementById(\'smtpModal\').showModal(); document.getElementById(\'smtpProvider\').value=\'google\'"')
            content += "\n" + modal_html
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

print("Dashboard templates updated with SMTP modal.")
