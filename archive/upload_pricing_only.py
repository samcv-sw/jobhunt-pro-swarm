import requests
import json
from _upload_to_pa import HEADERS, HEADERS_MUL, USERNAME, DOMAIN, API_BASE, upload_file_multipart, reload_webapp

status, text = upload_file_multipart("jobhunt/web/templates/pricing_v3.html", "web/templates/pricing_v3.html")
if status in (200, 201):
    print("OK 200 pricing_v3.html")
else:
    print("Failed to upload pricing_v3.html:", status, text)

print("\n=== Reloading webapp ===")
print(reload_webapp())
