import sqlite3
import os
import re
import csv
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/jobhunt_saas_v2.db'
CSV_PATH = r'C:\Users\samde\Downloads\JobHunt_Full_1200plus_Dispatches_Export.csv'

def clean_database():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=== STARTING DATABASE PURGE AND DEDUPLICATION ===")

    # 1. Identify & Purge Synthetic / Fake / Demo entries in campaign_emails
    cursor.execute("""
        DELETE FROM campaign_emails 
        WHERE LOWER(email_address) LIKE 'careers@ent%'
           OR LOWER(email_address) LIKE '%example.com'
           OR LOWER(email_address) LIKE '%test.com'
           OR LOWER(email_address) LIKE '%demo.com'
           OR LOWER(company_name) LIKE 'enterprise systems ent%'
           OR LOWER(company_name) LIKE 'test %'
           OR LOWER(company_name) LIKE 'demo %'
    """)
    deleted_ce_synth = cursor.rowcount
    print(f"Purged {deleted_ce_synth} synthetic/demo records from campaign_emails.")

    # 2. Identify & Purge Synthetic / Fake / Demo entries in multi_platform_apps
    cursor.execute("""
        DELETE FROM multi_platform_apps 
        WHERE LOWER(company) LIKE 'enterprise systems ent%'
           OR LOWER(company) LIKE 'test %'
           OR LOWER(company) LIKE 'demo %'
    """)
    deleted_mpa_synth = cursor.rowcount
    print(f"Purged {deleted_mpa_synth} synthetic/demo records from multi_platform_apps.")

    # 3. Deduplicate campaign_emails (Keep ONLY the earliest single send per email address)
    rows = cursor.execute("SELECT id, LOWER(TRIM(email_address)) as email FROM campaign_emails ORDER BY id ASC").fetchall()
    seen_emails = set()
    to_delete_ce = []
    for r in rows:
        email = r['email']
        if not email or email in seen_emails:
            to_delete_ce.append(r['id'])
        else:
            seen_emails.add(email)

    if to_delete_ce:
        cursor.executemany("DELETE FROM campaign_emails WHERE id = ?", [(id,) for id in to_delete_ce])
        print(f"Deduplicated {len(to_delete_ce)} duplicate dispatch records from campaign_emails.")
    else:
        print("Zero duplicate dispatches found in campaign_emails.")

    # 4. Deduplicate multi_platform_apps (Keep ONLY earliest single entry per company+job_title)
    mpa_rows = cursor.execute("SELECT id, LOWER(TRIM(company)) as comp, LOWER(TRIM(job_title)) as title FROM multi_platform_apps ORDER BY id ASC").fetchall()
    seen_mpa = set()
    to_delete_mpa = []
    for r in mpa_rows:
        key = (r['comp'], r['title'])
        if key in seen_mpa:
            to_delete_mpa.append(r['id'])
        else:
            seen_mpa.add(key)

    if to_delete_mpa:
        cursor.executemany("DELETE FROM multi_platform_apps WHERE id = ?", [(id,) for id in to_delete_mpa])
        print(f"Deduplicated {len(to_delete_mpa)} duplicate records from multi_platform_apps.")
    else:
        print("Zero duplicate records found in multi_platform_apps.")

    # 5. Create UNIQUE index on campaign_emails(LOWER(email_address)) to prevent future duplicate inserts at DB level
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_campaign_email_lower ON campaign_emails(LOWER(email_address))")
        print("Created UNIQUE index idx_unique_campaign_email_lower on campaign_emails.")
    except Exception as e:
        print(f"Notice creating index: {e}")

    conn.commit()

    # 6. Re-export clean CSV
    ce_rows = cursor.execute(
        "SELECT email_address, job_title, company_name, status, sent_at, opened_at, tracking_id FROM campaign_emails ORDER BY id DESC"
    ).fetchall()
    
    mpa_rows = cursor.execute(
        "SELECT platform, job_title, company, status, applied_at, url, id FROM multi_platform_apps ORDER BY id DESC"
    ).fetchall()

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["نوع التقديم", "البريد / المنصة", "المسمى الوظيفي", "اسم الشركة", "الحالة", "تاريخ الإرسال", "تاريخ الفتح", "معرف التتبع / الرابط"])

        for r in ce_rows:
            rd = dict(r)
            writer.writerow([
                "إيميل مباشر (Email)",
                rd.get("email_address") or "",
                rd.get("job_title") or "",
                rd.get("company_name") or "",
                rd.get("status") or "sent",
                rd.get("sent_at") or "",
                rd.get("opened_at") or "-",
                rd.get("tracking_id") or ""
            ])

        for r in mpa_rows:
            rd = dict(r)
            writer.writerow([
                f"منصة تلقائية ({rd.get('platform') or 'LinkedIn/Bayt'})",
                rd.get("platform") or "Multi-Platform",
                rd.get("job_title") or "",
                rd.get("company") or "",
                rd.get("status") or "applied",
                rd.get("applied_at") or "",
                "-",
                rd.get("url") or f"MPA-{rd.get('id')}"
            ])

    print(f"=== CLEAN CSV EXPORTED TO {CSV_PATH} ===")
    print(f"Total exported rows: {len(ce_rows) + len(mpa_rows)} (Emails: {len(ce_rows)}, MPA: {len(mpa_rows)})")

    conn.close()

if __name__ == '__main__':
    clean_database()
