import os, shutil

root = os.path.dirname(os.path.abspath(__file__))
backup = os.path.join(root, '_backups', 'cleanup_20260624')
os.makedirs(backup, exist_ok=True)

# Critical DBs to keep
keep = {
    'jobhunt_saas_v2.db', 'jobhunt_saas.db', 'jobhunt.db',
    'database.db', 'jobs.db', 'leads.db', 'hyper_jobs.db',
    'freelance_bids.db', 'campaigns.db', 'saas_v2.db'
}

db_files = [f for f in os.listdir(root) if f.endswith('.db')]
junk = [f for f in db_files if f not in keep]

total = 0
moved = 0
for f in junk:
    src = os.path.join(root, f)
    dst = os.path.join(backup, f)
    sz = os.path.getsize(src)
    total += sz
    if not os.path.exists(dst):
        shutil.move(src, dst)
        moved += 1

with open(os.path.join(backup, 'DB_CLEANUP_LOG.txt'), 'w') as log:
    log.write(f'DB Cleanup: 2026-06-24\n')
    log.write(f'Moved {moved} junk databases to backup\n')
    log.write(f'Saved: {total/1024:.1f} KB ({total/1048576:.2f} MB)\n')
    for f in junk:
        log.write(f'  {f}\n')
