import json, os

json_path = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\gmail_accounts.json"
data_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\data"
smtps_path = os.path.join(data_dir, "smtps.txt")

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        accounts = json.load(f)
    
    os.makedirs(data_dir, exist_ok=True)
    
    with open(smtps_path, "a", encoding="utf-8") as f:
        f.write("\n# Migrated from gmail_accounts.json\n")
        for acc in accounts:
            f.write(f"{acc['email']}:{acc['app_password']}\n")
    
    os.remove(json_path)
    print("Gmail accounts migrated to data/smtps.txt and json deleted.")
else:
    print("gmail_accounts.json not found.")
