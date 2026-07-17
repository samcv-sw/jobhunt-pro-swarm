import sys
import os

env_path = "/home/JHFGUF/jobhunt/.env"
if not os.path.exists(env_path):
    print(f"Error: .env not found at {env_path}")
    sys.exit(1)

with open(env_path, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

new_lines = []
has_sec = False
has_jwt = False
has_db = False

for line in lines:
    if line.startswith("SECRET_KEY="):
        line = "SECRET_KEY=9b743ad0bf90f3c647a61d8de9632ea68f90d069b15a4f9b8f90d069b15a4f9b"
        has_sec = True
    elif line.startswith("JWT_SECRET_KEY="):
        line = "JWT_SECRET_KEY=8f90d069b15a4f9b8f90d069b15a4f9b8f90d069b15a4f9b8f90d069b15a4f9b"
        has_jwt = True
    elif line.startswith("DATABASE_URL="):
        # Point DATABASE_URL directly to unified SQLite path to sync backend and web components
        line = "DATABASE_URL=sqlite+aiosqlite:////home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db"
        has_db = True
    new_lines.append(line)

if not has_sec:
    new_lines.append("SECRET_KEY=9b743ad0bf90f3c647a61d8de9632ea68f90d069b15a4f9b8f90d069b15a4f9b")
if not has_jwt:
    new_lines.append("JWT_SECRET_KEY=8f90d069b15a4f9b8f90d069b15a4f9b8f90d069b15a4f9b8f90d069b15a4f9b")
if not has_db:
    new_lines.append("DATABASE_URL=sqlite+aiosqlite:////home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db")

# Force override LOCAL_DATABASE_URL and DB_PATH to match as well
new_lines = [l for l in new_lines if not l.startswith("LOCAL_DATABASE_URL=") and not l.startswith("DB_PATH=")]
new_lines.append("LOCAL_DATABASE_URL=sqlite+aiosqlite:////home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db")
new_lines.append("DB_PATH=/home/JHFGUF/jobhunt/data/jobhunt_saas_v2.db")

with open(env_path, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")

print(".env updated successfully with unified SQLite database URL and DB_PATH!")
