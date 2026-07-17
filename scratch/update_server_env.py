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
for line in lines:
    if line.startswith("SECRET_KEY="):
        line = "SECRET_KEY=9b743ad0bf90f3c647a61d8de9632ea68f90d069b15a4f9b8f90d069b15a4f9b"
        has_sec = True
    elif line.startswith("JWT_SECRET_KEY="):
        line = "JWT_SECRET_KEY=8f90d069b15a4f9b8f90d069b15a4f9b8f90d069b15a4f9b8f90d069b15a4f9b"
        has_jwt = True
    new_lines.append(line)

if not has_sec:
    new_lines.append("SECRET_KEY=9b743ad0bf90f3c647a61d8de9632ea68f90d069b15a4f9b8f90d069b15a4f9b")
if not has_jwt:
    new_lines.append("JWT_SECRET_KEY=8f90d069b15a4f9b8f90d069b15a4f9b8f90d069b15a4f9b8f90d069b15a4f9b")

with open(env_path, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")

print(".env updated successfully with permanent keys!")
