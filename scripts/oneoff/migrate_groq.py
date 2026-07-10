import json, os
import logging
logger = logging.getLogger(__name__)

keys_path = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\groq_keys.json"
env_path = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.env"

if os.path.exists(keys_path):
    with open(keys_path, "r", encoding="utf-8") as f:
        keys = json.load(f)
    
    keys_str = ",".join(keys)
    
    # Append to .env
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"\n# Migrated from groq_keys.json\nGROQ_API_KEY={keys_str}\n")
    
    # Delete original
    os.remove(keys_path)
    logger.info("GROQ_API_KEY migrated successfully to .env and json deleted.")
else:
    logger.info("groq_keys.json not found.")
