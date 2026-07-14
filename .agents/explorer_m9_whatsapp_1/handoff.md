# Handoff Report: WhatsApp Bot Remote Control (Milestone 9)

## 1. Observation

### WhatsApp Integration Codebase
1. **`core/zero_cost_whatsapp.py`**: Contains `ZeroCostWhatsAppAutomator` that communicates with Meta's official WhatsApp Cloud API:
   - Line 21-22: Loads credentials from the environment:
     ```python
     self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
     self.phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
     ```
   - Line 24: Implements `send_whatsapp_message(...)`, which uses Meta's REST API endpoint `https://graph.facebook.com/v17.0/{self.phone_id}/messages` to send pre-formatted follow-up templates.
2. **`core/whatsapp_notifier.py`**: Used to generate wa.me deep links and forward alerts via Telegram:
   - Line 87: Sends notifications via Telegram using `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` rather than direct automated WhatsApp messages.

### Webhook and Router Management
1. **`web/routers/webhook_bot.py`**: An existing FastAPI router loaded dynamically by `web/app_v2.py`:
   - Line 20: Exposes `@router.post("/api/v1/webhook/social")` accepting a `WebhookPayload` with `user_phone`, `message_text`, and `platform`.
2. **`web/app_v2.py`**: Main PythonAnywhere server entrypoint:
   - Line 666-675: Automatically iterates and mounts all routers inside the `web.routers` directory:
     ```python
     for _, module_name, _ in pkgutil.iter_modules(web.routers.__path__):
         module = importlib.import_module(f"web.routers.{module_name}")
         if hasattr(module, "router"):
             app.include_router(module.router)
     ```
   - Line 1665-1668: Defines the `system_config` key-value table:
     ```python
     CREATE TABLE IF NOT EXISTS system_config (
         key TEXT PRIMARY KEY,
         value TEXT NOT NULL
     );
     INSERT OR IGNORE INTO system_config (key, value) VALUES ('panic_mode', 'false');
     ```
   - Line 401: Implements `_campaign_self_tick_loop()`, which checks database for pending campaigns and queues them for Celery.
3. **`backend/main.py`**: The container API server:
   - Line 145-148: Initializes `TelegramBot()` and starts `notifier`.
   - Line 469-484: Defines `@app.post("/webhook/telegram")` to process incoming Telegram messages using `bot_instance.process_webhook_update(...)`.

### Telegram Command Implementations
- **`core/telegram/bot.py`**: Implements remote control commands for the Telegram interface:
  - Line 1186: `/start` welcome keyboard (`cmd_start`).
  - Line 1333: `/status` system health score, uptime, and database metrics (`cmd_status`).
  - Line 1775: `/pause` changes `self._auto_running = False` (`cmd_pause`).
  - Line 3832: `/kill_switch` stops processes and cancels database queues (`cmd_kill_switch`).

### Configuration
- **`config.py`**: Defines candidate details:
  - Line 36: `CANDIDATE_PHONE = os.getenv("CANDIDATE_PHONE", "+961 71 019 053")`.

---

## 2. Logic Chain

1. **Meta WhatsApp Webhook Setup**: Meta Cloud API webhooks require a validation handshake (GET verification) and a POST route to receive messages. By creating a new FastAPI router file `web/routers/whatsapp_bot.py`, it will be dynamically loaded by the PythonAnywhere server (as seen in `web/app_v2.py:666`) and can be manually mapped in `backend/main.py` if needed.
2. **Access Control**: Commands sent from phone numbers other than the sanitized `CANDIDATE_PHONE` (e.g. `96171019053`) must be rejected to ensure security.
3. **State Management**: Using `self._auto_running` works for a single running instance (like the Telegram Bot class) but is fragile across multi-process container deployment and PythonAnywhere threads. Since `system_config` (seen in `web/app_v2.py:1665`) is a database-backed table, storing a setting like `campaign_runner_paused = 'true'` / `'false'` will coordinate pausing and resuming across Celery tasks and PythonAnywhere web processes cleanly.
4. **Integration with Campaign Loop**: Changing the campaign runner check inside `_campaign_self_tick_loop` and the main loop in `core/campaign_runner.py` to stop processing when `campaign_runner_paused` is `'true'` will implement instantaneous remote pausing.
5. **Generic Replies**: Meta allows free-form text responses within a 24-hour customer service window of a user's incoming message. Adding `send_text_message` using the `text` message body format to `ZeroCostWhatsAppAutomator` allows the bot to reply to command requests like `/status` with dynamic text.

---

## 3. Caveats

- **Meta Customer Service Window**: Free-form text message replies (responses to `/status`) will fail if it has been more than 24 hours since the user last messaged the WhatsApp bot number. However, since the commands themselves constitute incoming messages, this window is always open when responding to a command.
- **WhatsApp Webhook Verification**: The user must manually configure the Webhook URL and `WHATSAPP_VERIFY_TOKEN` in the Meta Developer Console for the handshake to succeed.

---

## 4. Conclusion

To implement Milestone 9 (WhatsApp Bot Remote Control), three code additions/changes are required:

### A. Extend `core/zero_cost_whatsapp.py`
Add a helper to send free-text messages (replies):
```python
async def send_text_message(self, phone_number: str, message: str) -> dict:
    """Send free-form text message via Meta API (within 24h window)."""
    if not self.access_token or not self.phone_id:
        logger.warning("WhatsApp API credentials missing. Simulating sending text message.")
        return {"status": "simulated", "body": message}

    url = f"https://graph.facebook.com/v17.0/{self.phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {self.access_token}",
        "Content-Type": "application/json",
    }
    formatted_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
    payload = {
        "messaging_product": "whatsapp",
        "to": formatted_phone,
        "type": "text",
        "text": {"body": message},
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code in (200, 201):
            return {"status": "success"}
        else:
            logger.error(f"WhatsApp send failed: {resp.text}")
            return {"status": "error", "error": resp.text}
```

### B. Create `web/routers/whatsapp_bot.py`
Create the webhook endpoints:
```python
import logging
import os
from fastapi import APIRouter, Request, Response, HTTPException
from core.pg_sqlite_shim import get_db
from core.zero_cost_whatsapp import whatsapp_automator
from config import CANDIDATE_PHONE

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/v1/webhook/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        return Response(content=params.get("hub.challenge"), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Forbidden")

@router.post("/api/v1/webhook/whatsapp")
async def receive_whatsapp_message(request: Request):
    try:
        body = await request.json()
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return {"status": "ok"}

        message = messages[0]
        sender_phone = message.get("from")
        message_text = message.get("text", {}).get("body", "").strip()

        # Sanitize authorization check
        candidate_phone_clean = CANDIDATE_PHONE.replace("+", "").replace(" ", "").replace("-", "")
        if sender_phone != candidate_phone_clean:
            return {"status": "unauthorized"}

        if message_text.startswith("/"):
            await handle_whatsapp_command(sender_phone, message_text)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"WhatsApp Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

async def handle_whatsapp_command(phone: str, text: str):
    parts = text.split(" ", 1)
    command = parts[0].lower()
    
    conn = get_db()
    try:
        if command in ("/start", "/resume"):
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('campaign_runner_paused', 'false')")
            conn.commit()
            await whatsapp_automator.send_text_message(phone, "▶️ Campaign processing resumed.")
        
        elif command == "/pause":
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('campaign_runner_paused', 'true')")
            conn.commit()
            await whatsapp_automator.send_text_message(phone, "⏸️ Campaign processing paused.")
        
        elif command == "/status":
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            campaigns = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
            emails_sent = conn.execute("SELECT COUNT(*) FROM campaign_emails WHERE status='sent'").fetchone()[0]
            
            paused_row = conn.execute("SELECT value FROM system_config WHERE key = 'campaign_runner_paused'").fetchone()
            is_paused = "PAUSED ⏸️" if (paused_row and paused_row["value"].lower() == "true") else "RUNNING 🟢"
            
            status_msg = (
                f"🩺 *System Status*\n\n"
                f"🔄 *Auto-Apply state:* {is_paused}\n"
                f"👤 *Users:* {users}\n"
                f"📦 *Campaigns:* {campaigns}\n"
                f"📬 *Emails Sent:* {emails_sent}\n"
            )
            await whatsapp_automator.send_text_message(phone, status_msg)
    finally:
        conn.close()
```

### C. Implement State Checks in loops
In `web/app_v2.py` inside `_campaign_self_tick_loop()`:
```python
# Before enqueuing tasks
with get_db() as _conn:
    paused_row = _conn.execute("SELECT value FROM system_config WHERE key = 'campaign_runner_paused'").fetchone()
    if paused_row and paused_row['value'].lower() == 'true':
        continue
```
In `core/campaign_runner.py` inside the sending loop:
```python
with get_db() as conn:
    row = conn.execute("SELECT value FROM system_config WHERE key = 'campaign_runner_paused'").fetchone()
    if row and row['value'].lower() == 'true':
        logger.warning(f"Campaign runner was paused. Halting campaign {campaign_id} execution.")
        return {"status": "paused", "sent": sent_count}
```

---

## 5. Verification Method

To verify these changes:
1. **Mock Meta's Verification**:
   Send a GET request simulating Meta's App Dashboard:
   `curl "http://localhost:8000/api/v1/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test_challenge"`
   Ensure the response is exactly `test_challenge` with status code 200.
2. **Mock Webhook Command**:
   POST a command update mimicking Meta API body payload containing `/pause` and verify that the database table `system_config` updates the key `campaign_runner_paused` to `'true'`.
3. **Loop Verification**:
   Trigger `_campaign_self_tick_loop()` (or run the FastAPI app) and verify that no campaigns are dispatched to Celery when `campaign_runner_paused` is `'true'`.
