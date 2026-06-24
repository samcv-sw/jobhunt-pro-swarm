import urllib.request
import urllib.parse
import json
import os
import sys
import time

# Google Drive API Endpoints
ABOUT_URL = "https://www.googleapis.com/drive/v3/about?fields=storageQuota"
FILES_URL = "https://www.googleapis.com/drive/v3/files"

def log(msg):
    print(f"[QUOTA-STORAGE] {msg}")

def get_access_token(client_id, client_secret, refresh_token):
    """Retrieve new OAuth2 access token using refresh token."""
    url = "https://oauth2.googleapis.com/token"
    payload = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("access_token")
    except Exception as e:
        log(f"Failed to refresh access token: {e}")
        return None

def check_quota_and_clean(access_token, folder_id):
    """Query Google Drive quota. If storage is tight, purge oldest files in folder_id."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 1. Check storage quota
    try:
        req = urllib.request.Request(ABOUT_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        quota = data.get("storageQuota", {})
        limit = int(quota.get("limit", 0))
        usage = int(quota.get("usage", 0))
        
        limit_gb = limit / (1024**3)
        usage_gb = usage / (1024**3)
        free_gb = limit_gb - usage_gb
        
        log(f"Current storage: {usage_gb:.2f} GB / {limit_gb:.2f} GB ({free_gb:.2f} GB Free)")
        
        # 2. Trigger clean up based on quota tier
        if limit_gb <= 20.0:  # Free tier (15 GB)
            if usage_gb >= 1.0:
                log("⚠️ STORAGE WARNING (15GB Free Tier): Usage exceeds 1.0 GB. Starting safe-purge...")
                # We want to delete files until l-remaining free space is at least limit_gb - 1.0 GB (meaning usage < 1.0 GB)
                purge_old_files(access_token, folder_id, safety_target_gb=limit_gb - 1.0, current_free_gb=free_gb)
            else:
                log("✓ Usage is under 1.0 GB. Storage level is safe.")
        else:  # Active 5 TB Subscription (or other paid tier)
            if free_gb < 10.0:  # If we have less than 10 GB free on 5 TB, clean up
                log("⚠️ STORAGE WARNING (Paid Tier): Less than 10GB free space. Starting safe-purge...")
                purge_old_files(access_token, folder_id, safety_target_gb=limit_gb - 5.0, current_free_gb=free_gb)
            else:
                log("✓ Storage level is safe.")
                
    except Exception as e:
        log(f"Error checking storage quota: {e}")

def purge_old_files(access_token, folder_id, safety_target_gb, current_free_gb):
    """Delete files from the specified folder, oldest first, until free space >= safety_target_gb."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Query files in the folder sorted by created time (oldest first)
    query = f"'{folder_id}' in parents and trashed = false"
    url = f"{FILES_URL}?q={urllib.parse.quote(query)}&orderBy=createdTime&fields=files(id,name,size,createdTime)"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            files_data = json.loads(resp.read().decode("utf-8"))
            
        files = files_data.get("files", [])
        if not files:
            log("No files found in the storage folder to delete.")
            return
            
        log(f"Found {len(files)} files in storage folder. Starting cleanup...")
        
        free_space_bytes = current_free_gb * (1024**3)
        target_bytes = safety_target_gb * (1024**3)
        
        deleted_count = 0
        for f in files:
            if free_space_bytes >= target_bytes:
                break
                
            file_id = f.get("id")
            name = f.get("name")
            size = int(f.get("size", 0))
            
            log(f"Deleting oldest file: '{name}' ({size / (1024**2):.2f} MB)...")
            
            # Perform delete
            del_url = f"{FILES_URL}/{file_id}"
            del_req = urllib.request.Request(del_url, headers=headers, method="DELETE")
            try:
                with urllib.request.urlopen(del_req, timeout=15) as del_resp:
                    if del_resp.status in (200, 204):
                        free_space_bytes += size
                        deleted_count += 1
            except Exception as del_err:
                log(f"Failed to delete {name}: {del_err}")
                
        log(f"Cleanup complete. Deleted {deleted_count} files. New free space estimation: {free_space_bytes / (1024**3):.2f} GB")
        
    except Exception as e:
        log(f"Error purging old files: {e}")

if __name__ == "__main__":
    # Get credentials from environment variables (configured via GitHub Secrets or .env)
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID") # Specific folder for backups/caches
    
    if not all([client_id, client_secret, refresh_token, folder_id]):
        log("Missing required environment variables for Google Drive safe storage. Skipping check.")
        sys.exit(0)
        
    token = get_access_token(client_id, client_secret, refresh_token)
    if token:
        check_quota_and_clean(token, folder_id)
