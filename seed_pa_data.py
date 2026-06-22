import sqlite3, json, random, uuid
from datetime import datetime, timedelta

DB = 'jobhunt_saas_v2.db'
JOBS = [
    ("JOB001","Senior Network Engineer","Cisco Systems","hr@cisco.com","Beirut","1200-1500 USD"),
    ("JOB002","Network Security Engineer","Fortinet","careers@fortinet.com","Dubai","8000-12000 USD"),
    ("JOB003","Cloud Network Architect","AWS","aws-jobs@amazon.com","Remote","9000-13000 USD"),
    ("JOB004","IT Infrastructure Manager","Bank Audi","hr@banqueaudi.com","Beirut","2000-3000 USD"),
    ("JOB005","Network Ops Lead","STC","careers@stc.com.sa","Riyadh","10000-15000 USD"),
    ("JOB006","Security Ops Analyst","Qatar Telecom","hr@ooredoo.qa","Doha","8000-12000 USD"),
    ("JOB007","Systems Engineer","Microsoft","careers@microsoft.com","Remote","10000-16000 USD"),
    ("JOB008","Network Engineer","DataTech","info@datatech.me","Beirut","1500-2500 USD"),
    ("JOB009","SOC Team Lead","Mobily","hr@mobily.com.sa","Jeddah","9000-13000 USD"),
    ("JOB010","Infrastructure Architect","Emirates NBD","careers@emiratesnbd.com","Dubai","12000-18000 USD"),
    ("JOB011","Network Admin","Alfa Telecom","hr@alfa.com.lb","Beirut","1500-2000 USD"),
    ("JOB012","IT Security Manager","Blom Bank","hr@blombank.com","Beirut","2500-4000 USD"),
    ("JOB013","Cloud Engineer","Google Cloud","careers@google.com","Remote","10000-15000 USD"),
    ("JOB014","Network Analyst","Ooredoo","hr@ooredoo.com.kw","Kuwait City","7000-10000 USD"),
    ("JOB015","Data Center Engineer","Equinix","careers@equinix.com","Dubai","8000-12000 USD"),
    ("JOB016","Telecom Specialist","Touch Lebanon","hr@touch.com.lb","Beirut","1800-2800 USD"),
    ("JOB017","Security Consultant","Kaspersky","jobs@kaspersky.com","Remote","9000-14000 USD"),
    ("JOB018","IT Ops Manager","Murex","hr@murex.com","Beirut","3000-4500 USD"),
    ("JOB019","DevOps Engineer","Oracle","careers@oracle.com","Remote","10000-15000 USD"),
    ("JOB020","Wireless Engineer","Etisalat","careers@etisalat.ae","Abu Dhabi","8000-11000 USD"),
    ("JOB021","Cybersecurity Engineer","DarkMatter","hr@darkmatter.ae","Dubai","12000-18000 USD"),
    ("JOB022","Network Planning Engineer","Zain","hr@zain.com","Kuwait City","6000-9000 USD"),
    ("JOB023","IT Consultant","PwC","careers@pwc.com","Dubai","10000-15000 USD"),
    ("JOB024","Infrastructure Lead","Byblos Bank","hr@byblosbank.com.lb","Beirut","2500-4000 USD"),
    ("JOB025","Platform Engineer","Salesforce","careers@salesforce.com","Remote","11000-16000 USD"),
]

def seed():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] > 0:
        print("Already has data, skipping")
        conn.close()
        return

    uid = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()

    # 1. user
    c.execute("INSERT INTO users(user_id,email,password_hash,name,phone,is_active,created_at) VALUES(?,?,?,?,?,?,?)",
              (uid,"samsalameh.cv@gmail.com","*SEEDED*","Sam Salameh","+96171019053",1,now))

    # 2. jobs
    for jid,title,company,email,loc,sal in JOBS:
        c.execute("INSERT INTO jobs(job_id,company,title,email,location,salary,source,status,match_score,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (jid,company,title,email,loc,sal,"linkedin","new",random.randint(65,98),
                   (datetime.now()-timedelta(days=random.randint(0,30))).isoformat()))

    # 3. orders
    oid = "ORD-" + str(uuid.uuid4())[:6]
    c.execute("INSERT INTO orders(order_id,user_id,package_type,company_count,amount_usd,payment_status,payment_method,created_at) VALUES(?,?,?,?,?,?,?,?)",
              (oid,uid,"tier",200,20,"completed","USDT",now))

    # 4. campaign
    cid = "CAMP-" + str(uuid.uuid4())[:6]
    c.execute("INSERT INTO campaigns(campaign_id,user_id,order_id,status,total_companies,sent_count,created_at) VALUES(?,?,?,?,?,?,?)",
              (cid,uid,oid,"active",100,50,now))

    # 5. wallet
    c.execute("INSERT INTO wallet_transactions(user_id,transaction_type,amount,balance_after,description,created_at) VALUES(?,?,?,?,?,?)",
              (uid,"deposit",50,50,"First deposit",now))

    conn.commit()
    conn.close()
    print("SEEDED: 1 user + 25 jobs + 1 order + 1 campaign + 1 wallet")

seed()
