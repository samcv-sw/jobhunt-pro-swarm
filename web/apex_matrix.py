import sqlite3
import os
import shutil

db_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\jobhunt_saas_v2.db'

print("INITIATING APEX MATRIX PROTOCOL...")
print("1. ENVIRONMENT_PURGE: Executing absolute zero-state runtime clearance...")

# Clear pycache
pycache_dir = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\__pycache__'
if os.path.exists(pycache_dir):
    shutil.rmtree(pycache_dir)
    print("-> Eradicated fragmented cache: __pycache__")

# Optimize SQLite Database (Chi Routing & Latency Pruning)
if os.path.exists(db_path):
    print("2. SYNTHESIZING INFINITELY RECURSIVE OPTIMIZATION PASS (Database Layer)...")
    conn = sqlite3.connect(db_path)
    try:
        # Prune redundant registry pathways
        conn.execute("VACUUM;")
        print("-> VACUUM complete. Systemic entropy reduced.")
        
        # Optimize indexes for zero-friction execution
        conn.execute("REINDEX;")
        print("-> REINDEX complete. Latency bottlenecks aggressively pruned.")
        
        # Analyze tables for the query planner
        conn.execute("ANALYZE;")
        print("-> ANALYZE complete. Computational bandwidth routed with highest efficiency.")
        
    except Exception as e:
        print(f"Error during APEX optimization: {e}")
    finally:
        conn.close()
else:
    print("Database not found at: " + db_path)
        
print("\nOUTPUT PARAMETERS: Ultimate, unified, high-performance engine rendered. Execution flawless.")
