import os
from sqlalchemy import create_engine, text
from core.database import Base

sqlite_url = "sqlite:///jobhunt_saas_v2.db"
neon_sync_url = "postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require"

sqlite_engine = create_engine(sqlite_url)
neon_engine = create_engine(neon_sync_url)

def migrate():
    print("Creating tables in Neon Postgres...")
    Base.metadata.create_all(neon_engine)
    print("Tables created.")

    with sqlite_engine.connect() as sqlite_conn:
        with neon_engine.begin() as neon_conn:
            for table in Base.metadata.sorted_tables:
                print(f"Migrating table: {table.name}...")
                
                # Delete existing data in neon to avoid duplicate conflicts if re-running
                neon_conn.execute(table.delete())
                
                try:
                    # Get actual columns present in SQLite
                    columns_query = sqlite_conn.execute(text(f"PRAGMA table_info({table.name})")).fetchall()
                    sqlite_cols = [col[1] for col in columns_query]
                    
                    if not sqlite_cols:
                        print(f" -> Skipping {table.name}, table doesn't exist in source.")
                        continue
                    
                    # Read all data from sqlite
                    rows = sqlite_conn.execute(text(f"SELECT * FROM {table.name}")).mappings().fetchall()
                    if rows:
                        # Insert into neon using only the columns that exist in SQLite
                        dicts = [dict(row) for row in rows]
                        neon_conn.execute(
                            table.insert(),
                            dicts
                        )
                    print(f" -> Migrated {len(rows)} rows to {table.name}.")
                except Exception as e:
                    print(f" -> Error migrating {table.name}: {e}")
                
    print("Migration complete! You are now globally synced.")

if __name__ == "__main__":
    migrate()
