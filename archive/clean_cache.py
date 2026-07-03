import sqlite3
import os
import re
import sys

# Ensure console output handles unicode or fallbacks gracefully
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

unresolved_placeholders = [
    '{first_name}', '{company}', '{position}', '{title}', '{company_name}',
    '[Company Name]', '[Recruiter Name]', '[Job Title]', '[Insert',
    '<first_name>', '<company>', '<position>'
]

def is_invalid(text):
    if not text:
        return False
    has_unresolved = any(placeholder.lower() in text.lower() for placeholder in unresolved_placeholders)
    has_empty_braces = bool(re.search(r'\{\s*\}|\[\s*\]|<\s*>', text))
    return has_unresolved or has_empty_braces

def clean_database(db_path):
    if not os.path.exists(db_path):
        return
    
    # Print only the filename to avoid path encoding issues
    filename = os.path.basename(db_path)
    print(f"Checking database: {filename}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if semantic_cache table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='semantic_cache'")
        if not cursor.fetchone():
            conn.close()
            return
        
        # Select all entries to inspect
        cursor.execute("SELECT id, prompt_hash, response_text FROM semantic_cache")
        rows = cursor.fetchall()
        
        to_delete = []
        for row_id, prompt_hash, response_text in rows:
            if is_invalid(response_text):
                to_delete.append((row_id, prompt_hash))
                
        if to_delete:
            print(f"  Found {len(to_delete)} invalid cache entries in {filename}.")
            for row_id, prompt_hash in to_delete:
                cursor.execute("DELETE FROM semantic_cache WHERE id = ?", (row_id,))
            conn.commit()
            print(f"  Successfully deleted {len(to_delete)} invalid entries.")
        else:
            print("  No invalid cache entries found.")
            
        conn.close()
    except Exception as e:
        print(f"  Error cleaning {filename}: {e}")

def main():
    # Use relative path to avoid unicode encoding problems in path representation
    workspace_dir = "."
    for root, dirs, files in os.walk(workspace_dir):
        # Skip virtual env directories
        if ".venv" in root or ".venv2" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(('.db', '.sqlite', '.sqlite3')):
                db_path = os.path.join(root, file)
                clean_database(db_path)

if __name__ == '__main__':
    main()
