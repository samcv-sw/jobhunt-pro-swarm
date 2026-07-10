"""
Supabase REST API shim - replaces psycopg2 for direct PostgreSQL access.
Uses service_role key + Supabase REST API (PostgREST).
Same interface as pg_sqlite_shim.py for drop-in replacement.
"""

import logging
import os
import re
import urllib.parse

import requests

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://zfvzqutgpdbsievsclhn.supabase.co"
)
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BACKEND = "supabase_rest"
_headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


class OperationalError(Exception):
    pass


class IntegrityError(Exception):
    pass


class SupabaseCursor:
    """Mimics sqlite3 cursor but uses Supabase REST API."""

    def __init__(self, table=None):
        self._table = table
        self._rows = []
        self._row_index = 0
        self._description = None
        self.lastrowid = None

    def _parse_sql(self, query, params=None):
        """Parse simple SQL statements and convert to REST API calls.
        Handles: SELECT, INSERT, UPDATE, DELETE, PRAGMA
        """
        query = query.strip()
        if not query:
            return None, None

        # Ignore PRAGMA statements
        if query.upper().startswith("PRAGMA"):
            return "PRAGMA", None

        # Simple parser for common patterns
        upper = query.upper()

        # SELECT parsing
        if upper.startswith("SELECT"):
            return self._parse_select(query, params)

        # INSERT parsing
        if upper.startswith("INSERT"):
            return self._parse_insert(query, params)

        # UPDATE parsing
        if upper.startswith("UPDATE"):
            return self._parse_update(query, params)

        # DELETE parsing
        if upper.startswith("DELETE"):
            return self._parse_delete(query, params)

        # For unsupported queries, we'll try to pattern-match
        if upper.startswith("CREATE TABLE"):
            return "CREATE", query
        if upper.startswith("ALTER TABLE"):
            return "ALTER", query

        # If we can't parse it, try as raw
        return "RAW", query

    def _extract_table_from_sql(self, query):
        """Extract table name from SQL."""
        upper = query.upper().strip()
        patterns = [
            r"(?:FROM|INTO|UPDATE|TABLE)\s+`?(\w+)`?",
            r"INSERT\s+(?:INTO\s+)?`?(\w+)`?",
        ]
        for pat in patterns:
            m = re.search(pat, upper, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    def _parse_where(self, query):
        """Extract WHERE conditions: col=?, col=? OR col=val"""
        where_match = re.search(
            r"WHERE\s+(.+?)(?:ORDER BY|LIMIT|OFFSET|$)", query, re.IGNORECASE
        )
        if not where_match:
            return {}, ""

        where_clause = where_match.group(1).strip()
        # Remove trailing keywords
        for kw in ["ORDER BY", "LIMIT", "OFFSET", ";"]:
            idx = where_clause.upper().find(kw)
            if idx > 0:
                where_clause = where_clause[:idx].strip()

        # Parse individual conditions: col=? OR col=value
        conditions = {}
        parts = re.findall(r"(\w+)\s*=\s*(\?|%s)", where_clause)
        for col, _ in parts:
            conditions[col] = None  # placeholder, will be filled with params
        return conditions, where_clause

    def _build_filter(self, col, val):
        """Build PostgREST filter parameter."""
        if val is None:
            return f"{col}=is.null"
        if isinstance(val, bool):
            return f"{col}=eq.{str(val).lower()}"
        if isinstance(val, (int, float)):
            return f"{col}=eq.{val}"
        return f"{col}=eq.{urllib.parse.quote(str(val))}"

    def _parse_select(self, query, params):
        """Convert SELECT to REST API call."""
        # Extract columns
        cols_match = re.search(
            r"SELECT\s+(.*?)\s+FROM", query, re.IGNORECASE | re.DOTALL
        )
        select_cols = "*"
        if cols_match:
            cols = cols_match.group(1).strip()
            if cols != "*":
                select_cols = cols

        # Extract table
        from_match = re.search(r"FROM\s+`?(\w+)`?", query, re.IGNORECASE)
        if not from_match:
            return None, None
        table = from_match.group(1)

        # Build URL
        url = f"{SUPABASE_URL}/rest/v1/{table}"

        # Add select parameter
        if select_cols != "*":
            url += f"?select={urllib.parse.quote(select_cols)}"

        # Parse WHERE clause
        conditions, _ = self._parse_where(query)
        if conditions:
            sep = "&" if "?" in url else "?"
            for i, col in enumerate(conditions.keys()):
                val = params[i] if params and i < len(params) else None
                url += f"{sep}{self._build_filter(col, val)}"
                sep = "&"

        # Parse ORDER BY
        order_match = re.search(r"ORDER BY\s+(\w+)\s*(ASC|DESC)?", query, re.IGNORECASE)
        if order_match:
            col = order_match.group(1)
            direction = "asc"
            if order_match.group(2):
                direction = order_match.group(2).lower()
            sep = "&" if "?" in url else "?"
            url += f"{sep}order={col}.{direction}"

        # Parse LIMIT
        limit_match = re.search(r"LIMIT\s+(\d+)", query, re.IGNORECASE)
        if limit_match:
            sep = "&" if "?" in url else "?"
            url += f"{sep}limit={limit_match.group(1)}"

        # Parse OFFSET
        offset_match = re.search(r"OFFSET\s+(\d+)", query, re.IGNORECASE)
        if offset_match:
            sep = "&" if "?" in url else "?"
            url += f"{sep}offset={offset_match.group(1)}"

        return "SELECT", {"method": "GET", "url": url, "table": table}

    def _parse_insert(self, query, params):
        """Convert INSERT to REST API call."""
        table_match = re.search(r"INSERT\s+(?:INTO\s+)?`?(\w+)`?", query, re.IGNORECASE)
        if not table_match:
            return None, None
        table = table_match.group(1)

        # Extract columns
        cols_match = re.search(r"\(([^)]+)\)", query)
        if not cols_match:
            return None, None
        cols = [c.strip().strip('"`') for c in cols_match.group(1).split(",")]

        # Build JSON body
        row = {}
        for i, col in enumerate(cols):
            val = params[i] if params and i < len(params) else None
            row[col] = val

        return "INSERT", {
            "method": "POST",
            "url": f"{SUPABASE_URL}/rest/v1/{table}",
            "json": row,
            "table": table,
        }

    def _parse_update(self, query, params):
        """Convert UPDATE to REST API call."""
        table_match = re.search(r"UPDATE\s+`?(\w+)`?", query, re.IGNORECASE)
        if not table_match:
            return None, None
        table = table_match.group(1)

        # Extract SET clause
        set_match = re.search(
            r"SET\s+(.+?)(?:WHERE|$)", query, re.IGNORECASE | re.DOTALL
        )
        if not set_match:
            return None, None
        set_clause = set_match.group(1).strip()

        # Parse col1=?, col2=?
        set_pairs = re.findall(r"(\w+)\s*=\s*(\?|%s)", set_clause)
        set_cols = [p[0] for p in set_pairs]

        # Build JSON body
        updates = {}
        for i, col in enumerate(set_cols):
            val = params[i] if params and i < len(params) else None
            updates[col] = val

        # Parse WHERE
        conditions, _ = self._parse_where(query)
        url = f"{SUPABASE_URL}/rest/v1/{table}?"
        sep = ""
        for i, col in enumerate(conditions.keys()):
            val_idx = len(set_cols) + i
            val = params[val_idx] if params and val_idx < len(params) else None
            url += f"{sep}{self._build_filter(col, val)}"
            sep = "&"

        return "UPDATE", {
            "method": "PATCH",
            "url": url,
            "json": updates,
            "table": table,
        }

    def _parse_delete(self, query, params):
        """Convert DELETE to REST API call."""
        table_match = re.search(r"DELETE\s+FROM\s+`?(\w+)`?", query, re.IGNORECASE)
        if not table_match:
            return None, None
        table = table_match.group(1)

        # Parse WHERE
        conditions, _ = self._parse_where(query)
        url = f"{SUPABASE_URL}/rest/v1/{table}?"
        sep = ""
        for i, col in enumerate(conditions.keys()):
            val = params[i] if params and i < len(params) else None
            url += f"{sep}{self._build_filter(col, val)}"
            sep = "&"

        return "DELETE", {"method": "DELETE", "url": url, "table": table}

    def execute(self, query, params=None):
        """Execute a SQL query via Supabase REST API."""
        if params is not None and not isinstance(params, (list, tuple)):
            params = (params,)

        action, info = self._parse_sql(query, params)

        if action is None:
            raise OperationalError(f"Cannot parse query: {query[:100]}")

        if action == "PRAGMA":
            self._rows = []
            self.lastrowid = None
            return self

        if action == "CREATE":
            # Tables are already created via SQL Editor
            self._rows = []
            return self

        if action == "ALTER":
            self._rows = []
            return self

        if action == "RAW":
            # Try to execute raw SQL via custom function
            logger.warning(f"Unsupported query type, skipping: {query[:100]}")
            self._rows = []
            return self

        try:
            method = info["method"]
            url = info["url"]
            headers = dict(_headers)
            session = _get_session()

            if method == "GET":
                headers["Accept"] = "application/json"
                r = session.get(url, headers=headers, timeout=10)
            elif method == "POST":
                headers["Prefer"] = "return=representation"
                r = session.post(
                    url, headers=headers, json=info.get("json", {}), timeout=10
                )
            elif method == "PATCH":
                headers["Prefer"] = "return=representation"
                r = session.patch(
                    url, headers=headers, json=info.get("json", {}), timeout=10
                )
            elif method == "DELETE":
                headers["Prefer"] = "return=representation"
                r = session.delete(url, headers=headers, timeout=10)
            else:
                raise OperationalError(f"Unknown method: {method}")

            if r.status_code >= 400:
                err = r.text[:200]
                if "duplicate key" in err.lower() or "unique" in err.lower():
                    raise IntegrityError(err)
                raise OperationalError(f"Supabase API error: {r.status_code} - {err}")

            # Parse response
            if r.status_code == 204 or not r.text.strip():
                self._rows = []
                self.lastrowid = None
            else:
                data = r.json()
                if isinstance(data, list):
                    self._rows = data
                    if action == "INSERT" and data:
                        self.lastrowid = data[0].get("id")
                elif isinstance(data, dict):
                    self._rows = [data]
                    self.lastrowid = data.get("id")
                else:
                    self._rows = []

        except (IntegrityError, OperationalError):
            raise
        except Exception as e:
            raise OperationalError(f"Supabase request failed: {e}")

        return self

    def fetchone(self):
        if self._row_index < len(self._rows):
            row_data = self._rows[self._row_index]
            self._row_index += 1
            return DictRow(row_data)
        return None

    def fetchall(self):
        rows = [DictRow(r) for r in self._rows]
        self._row_index = len(self._rows)
        return rows

    def fetchmany(self, size=None):
        remaining = self._rows[self._row_index :]
        if size and size < len(remaining):
            remaining = remaining[:size]
        self._row_index += len(remaining)
        return [DictRow(r) for r in remaining]

    def close(self):
        pass


class DictRow:
    """Row class that supports both dict-style and attribute-style access, like sqlite3.Row."""

    def __init__(self, data):
        self._data = data or {}

    def __getitem__(self, key):
        if isinstance(key, int):
            keys = list(self._data.keys())
            if key < len(keys):
                return self._data[keys[key]]
            raise IndexError(f"Index {key} out of range")
        return self._data.get(key)

    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._data.get(name)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return list(self._data.keys())

    def values(self):
        return list(self._data.values())

    def __iter__(self):
        return iter(self._data.values())

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return str(self._data)


class SupabaseConnection:
    """Mimics sqlite3 connection but uses Supabase REST API."""

    def __init__(self):
        self.closed = False
        self.row_factory = None

    def execute(self, query, params=None):
        cursor = SupabaseCursor()
        return cursor.execute(query, params)

    def executescript(self, script):
        cursor = SupabaseCursor()
        for statement in script.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                except Exception:
                    pass
        return cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.closed = True

    def cursor(self):
        return SupabaseCursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def connect(db_path=None, **kwargs):
    """Connect to Supabase via REST API (no direct PostgreSQL needed).
    Accepts extra kwargs for compatibility with sqlite3.connect()."""
    global BACKEND
    BACKEND = "supabase_rest"
    logger.info(f"[DB] Connected to Supabase REST API ({SUPABASE_URL})")
    return SupabaseConnection()


def get_backend():
    return BACKEND


# Compatibility - export these at module level
OperationalError = OperationalError
IntegrityError = IntegrityError
Row = DictRow
Connection = SupabaseConnection
