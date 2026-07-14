APP_FILE = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\app_v2.py"

with open(APP_FILE, encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "content_html = render_template(\"tracking_analytics.html\"," in line:
        skip = True
        new_lines.append("""        content_html = render_template("tracking_analytics.html", 
                request=request,
                user=None,
                total_sent=total_sent_human,
                delivered=f"{delivered:,}" if delivered > 999 else str(delivered),
                opened=f"{opened:,}" if opened > 999 else str(opened),
                replied=f"{replied:,}" if replied > 999 else str(replied),
                bounced=str(bounced),
                open_rate=f"{open_rate}%",
                response_rate=f"{response_rate}%",
                bounce_rate=f"{bounce_rate}%",
                open_rate_raw=open_rate,
                response_rate_raw=response_rate,
                bounce_rate_raw=bounce_rate,
                per_campaign=per_campaign,
                total_unique=len(per_campaign),
                today=datetime.now().strftime("%b %d, %Y")
        )
        user_id_val = get_verified_user_id(request)
        if not user_id_val:
            user_id_val = "admin"
        return HTMLResponse(_build_dashboard_shell(None, user_id_val, content_html, "Tracking Analytics", "tracking-analytics"))
""")
    if skip and "except Exception as e:" in line:
        skip = False

    if not skip:
        new_lines.append(line)

with open(APP_FILE, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
