#!/bin/bash
# ============================================
# JobHunt Pro - PythonAnywhere Deploy Script
# Run this on PA Bash console:
#   bash pa_deploy.sh
# ============================================
set -e

echo "========================================"
echo "  JobHunt Pro PA Deployment"
echo "========================================"

cd ~/jobhunt || { echo "❌ jobhunt directory not found"; exit 1; }

echo ""
echo "1. Pulling latest code from GitHub..."
git fetch origin main
git reset --hard origin/main
echo "   ✅ Code updated"

echo ""
echo "2. Installing/updating dependencies..."
pip install -r requirements.txt --quiet 2>&1 | tail -1
echo "   ✅ Dependencies installed"

echo ""
echo "3. Checking database..."
DB="jobhunt_saas_v2.db"
if [ -f "$DB" ]; then
    echo "   ✅ Database exists ($(du -h $DB | cut -f1))"
    # Check jobs table
    python3 -c "
import sqlite3
conn = sqlite3.connect('$DB')
tables = [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]
if 'jobs' in tables:
    cnt = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    print(f'   ✅ Jobs table: {cnt} records')
else:
    print('   ❌ Jobs table missing - running repair...')
    conn.close()
    import subprocess
    subprocess.run(['python3', '_repair_db.py'])
"
else:
    echo "   ❌ No database found - creating..."
    python3 -c "from core.database import Database; import asyncio; asyncio.run(Database().create_tables())"
fi

echo ""
echo "4. Running seed scripts..."
python3 _seed_all.py 2>&1 | tail -5
echo "   ✅ Seed complete"

echo ""
echo "5. Creating .env from template..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || echo "   ⚠️ No .env.example found, creating minimal .env"
    # Create minimal .env if needed
    if [ ! -f ".env" ]; then
        cat > .env << 'ENVEOF'
GROQ_API_KEY=
TELEGRAM_BOT_TOKEN=8679211757:AAF_6HZaYRaVG-kCshDe9yqV9o_zL1nFhik
TELEGRAM_CHAT_ID=6639482672
GMAIL_SMTP_USER_1=samatou683@gmail.com
GMAIL_APP_PASSWORD_1=
BREVO_SMTP_LOGIN=
BREVO_SMTP_PASSWORD=
DB_PATH=jobhunt_saas_v2.db
SECRET_KEY=jobhunt-pro-production-2026
DRY_RUN=false
CLOUD_MODE=true
ENVEOF
    fi
fi
echo "   ✅ .env ready (check API keys)"

echo ""
echo "6. Testing imports..."
python3 -c "
import sys
sys.path.insert(0, '.')
from core.database import Database
print('   ✅ Database module loads')
import asyncio
asyncio.run(Database().create_tables())
print('   ✅ Tables created/verified')
" 2>&1
echo "   ✅ All imports pass"

echo ""
echo "7. Reloading web app..."
curl -s -X POST "https://www.pythonanywhere.com/api/v0/user/JHFGUF/webapps/jhfguf.pythonanywhere.com/reload/" \
  -H "Authorization: Token 7e7ad272cc2d4470e8078fca29dfacf301fb01fe" \
  > /dev/null && echo "   ✅ Web app reloaded"
echo ""
echo "========================================"
echo "  ✅ DEPLOYMENT COMPLETE"
echo "  Visit: https://jhfguf.pythonanywhere.com"
echo "========================================"
