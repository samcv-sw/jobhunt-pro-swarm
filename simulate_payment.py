import hmac
import hashlib
import json
import requests
import time

IPN_SECRET = "hCGQjbcilPsaJQkW073hfzg5ziDyszfl"
WEBHOOK_URL = "https://olympus-webhook.samsalameh-cv.workers.dev/api/v1/webhook/nowpayments"
TELEGRAM_ID = "6639482672"

payload_dict = {
    "order_id": f"{TELEGRAM_ID}_{int(time.time())}",
    "payment_status": "finished"
}

# Cloudflare worker sorts keys:
sorted_keys = sorted(payload_dict.keys())
sorted_obj = {k: payload_dict[k] for k in sorted_keys}

# The javascript JSON.stringify does not have spaces between keys/values
message = json.dumps(sorted_obj, separators=(',', ':'))

signature = hmac.new(
    IPN_SECRET.encode('utf-8'),
    message.encode('utf-8'),
    hashlib.sha512
).hexdigest()

print(f"Payload: {message}")
print(f"Signature: {signature}")

headers = {
    "Content-Type": "application/json",
    "x-nowpayments-sig": signature
}

print("Firing POST to Cloudflare...")
resp = requests.post(WEBHOOK_URL, data=message, headers=headers)
print(f"Response Code: {resp.status_code}")
print(f"Response Body: {resp.text}")
