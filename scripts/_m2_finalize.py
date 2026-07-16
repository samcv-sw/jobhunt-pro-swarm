"""M2 finalize: register all routers + strip duplicate inline routes/models from backend/main.py.

Preserves the re-export block (lines ~45-57) so test imports from backend.main keep working.
"""
import io

PATH = "backend/main.py"

with io.open(PATH, "r", encoding="utf-8") as fh:
    lines = fh.readlines()

# Anchor 1: the only currently-registered router
billing_idx = None
for i, ln in enumerate(lines):
    if ln.strip() == "app.include_router(billing_router)":
        billing_idx = i
        break
assert billing_idx is not None, "billing_router include anchor missing"

# Anchor 2: first inline import that belongs only to the duplicate block
remove_idx = None
for i, ln in enumerate(lines):
    if ln.strip() == "from datetime import UTC":
        remove_idx = i
        break
assert remove_idx is not None, "datetime import anchor missing"

# Everything from billing_idx+1 .. remove_idx-1 is blank/inline-import padding;
# everything from remove_idx .. EOF is duplicate inline models + routes (now in routers).
REGISTRATIONS = (
    "app.include_router(billing_router)\n"
    "app.include_router(accounts_router)\n"
    "app.include_router(analytics_router)\n"
    "app.include_router(admin_router)\n"
    "app.include_router(cover_letters_router)\n"
    "app.include_router(emails_router)\n"
    "app.include_router(health_router)\n"
    "app.include_router(referral_router)\n"
    "app.include_router(scraping_router)\n"
    "app.include_router(telegram_router)\n"
    "app.include_router(unsubscribe_router)\n"
    "app.include_router(webhooks_router)\n"
    "app.include_router(websocket_router)\n"
)

new_lines = lines[:billing_idx] + [REGISTRATIONS]

with io.open(PATH, "w", encoding="utf-8") as fh:
    fh.writelines(new_lines)

print(f"SUCCESS: old={len(lines)} new={len(new_lines)}")
