import logging
import os
import sqlite3
import sys

logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.pg_sqlite_shim import PgConnectionWrapper, convert_sql


def migrate():
    sqlite_db_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "pa_db.sqlite")
    )
    if not os.path.exists(sqlite_db_path):
        logger.debug(f"SQLite DB not found at {sqlite_db_path}")
        return

    logger.debug("Connecting to SQLite...")
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    logger.debug("Connecting to PostgreSQL...")
    try:
        pg_conn = PgConnectionWrapper()
    except Exception as e:
        logger.debug(f"Failed to connect to PG: {e}")
        return

    sqlite_cur.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = sqlite_cur.fetchall()

    for table in tables:
        name = table["name"]
        sql = table["sql"]
        if not sql:
            continue

        logger.debug(f"\nCreating table schema: {name}")
        pg_sql = convert_sql(sql)
        try:
            pg_conn.execute(f"DROP TABLE IF EXISTS {name} CASCADE")
            pg_conn.execute(pg_sql)
            pg_conn.commit()
        except Exception as e:
            logger.debug(f"Notice (table {name} might exist): {e}")
            pg_conn.rollback()

    for table in tables:
        name = table["name"]
        logger.debug(f"Migrating data for table: {name}...")

        sqlite_cur.execute(f"SELECT * FROM {name}")
        rows = sqlite_cur.fetchall()

        if not rows:
            logger.debug(f"  No data in {name}")
            continue

        columns = list(rows[0].keys())
        col_names = ", ".join(columns)

        insert_sql = (
            f"INSERT INTO {name} ({col_names}) VALUES %s ON CONFLICT DO NOTHING"
        )

        values_list = []
        for row in rows:
            values = list(row)
            if name == "wallet_transactions" and len(values) > 4:
                # Force balance_after (index 4) to be float, else 0.0
                try:
                    values[4] = float(values[4])
                except (ValueError, TypeError):
                    values[4] = 0.0
            for i, col in enumerate(columns):
                if col == "updated_at" and values[i] is None:
                    values[i] = "1970-01-01 00:00:00"
            values_list.append(tuple(values))

        try:
            import psycopg2.extras

            cur = pg_conn.conn.cursor()
            psycopg2.extras.execute_values(cur, insert_sql, values_list)
            logger.debug(f"  Inserted {len(values_list)} new rows into {name}")
        except Exception as e:
            logger.debug(f"  Failed bulk insert for {name}: {e}")
            pg_conn.rollback()

    logger.debug("\nMigration Complete!")


if __name__ == "__main__":
    migrate()
