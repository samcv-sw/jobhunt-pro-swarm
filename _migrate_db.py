import sqlite3

def add_column(conn, table, column, definition):
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        print(f"Added {column}")
    except Exception as e:
        print(f"Column {column} probably exists: {e}")

def migrate(db_path):
    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    
    add_column(conn, "users", "oauth_provider", "TEXT")
    add_column(conn, "users", "oauth_access_token", "TEXT")
    add_column(conn, "users", "oauth_refresh_token", "TEXT")
    add_column(conn, "users", "oauth_expires_at", "REAL")
    
    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate("jobhunt_saas_v2.db")
