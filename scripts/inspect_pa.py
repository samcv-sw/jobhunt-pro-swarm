import re
import sys
sys.path.append('scripts')
import pythonanywhere_auto_extend as pa

ext = pa.PythonAnywhereAutoExtender()
login_url = "https://www.pythonanywhere.com/login/"
r_get = ext.session.get(login_url)
m = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r_get.text)
csrf_token = m.group(1) if m else ""

login_data = {
    "csrfmiddlewaretoken": csrf_token,
    "auth-username": ext.username,
    "auth-password": ext.password,
    "login_view-current_step": "auth"
}
r_login = ext.session.post(login_url, data=login_data, headers={"Referer": login_url})
if "token" in r_login.text or "2fa" in r_login.url.lower():
    totp = pa.generate_totp_token(ext.totp_secret)
    m2 = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r_login.text)
    csrf_2fa = m2.group(1) if m2 else csrf_token
    ext.session.post(login_url, data={"csrfmiddlewaretoken": csrf_2fa, "2fa-token": totp, "login_view-current_step": "2fa"}, headers={"Referer": r_login.url})

# Get Web tab HTML
r_web = ext.session.get("https://www.pythonanywhere.com/user/JHFGUF/webapps/")
forms = re.findall(r'<form[^>]*action="([^"]*)"[^>]*>', r_web.text)
print("Forms on web tab:", forms)
buttons = re.findall(r'<button[^>]*>([^<]+)</button>', r_web.text)
print("Buttons on web tab:", buttons)
inputs = re.findall(r'<input[^>]*name="([^"]+)"[^>]*>', r_web.text)
print("Inputs on web tab:", set(inputs))

# Check Account page tabs
r_acc = ext.session.get("https://www.pythonanywhere.com/user/JHFGUF/account/")
acc_links = re.findall(r'href="([^"]*api_token[^"]*)"', r_acc.text)
print("API Token links:", acc_links)
