"""
services/sell.py — Service Subscription Sell/Transfer Engine

Allows users to sell or transfer their active service subscriptions
to other users. Validates ownership, handles wallet credit transfers,
and updates the database atomically.

Usage:
    python -m services.sell --order-id ORD-123 --target-email user@example.com
    python -m services.sell --order-id ORD-123 --target-email user@example.com --price 15.0
    python -m services.sell --list-own user_id_abc
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import uuid
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# ── Database ────────────────────────────────────────────────────────────────

def _get_db_path() -> str:
    """Resolve the SQLite database path from environment or default."""
    return os.getenv(
        "DATABASE_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "app.db"),
    )


def _get_conn() -> sqlite3.Connection:
    """Open a new database connection with WAL mode."""
    db_path = _get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Core Logic ──────────────────────────────────────────────────────────────

SELLABLE_STATUSES = frozenset({"paid", "delivered", "active"})


def get_user_by_email(email: str, conn: sqlite3.Connection | None = None) -> dict[str, Any] | None:
    """Look up a user by email address."""
    close = conn is None
    if conn is None:
        conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT user_id, email, wallet_balance FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        if close:
            conn.close()


def get_order(order_id: str, conn: sqlite3.Connection | None = None) -> dict[str, Any] | None:
    """Fetch a single order by its ID."""
    close = conn is None
    if conn is None:
        conn = _get_conn()
    try:
        row = conn.execute(
            """SELECT order_id, user_id, order_type, amount_usd, payment_status,
                      payment_method, created_at, description
               FROM orders WHERE order_id = ?""",
            (order_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        if close:
            conn.close()


def list_orders_for_user(user_id: str, conn: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
    """List all sellable orders belonging to a user."""
    close = conn is None
    if conn is None:
        conn = _get_conn()
    try:
        placeholders = ",".join("?" for _ in SELLABLE_STATUSES)
        rows = conn.execute(
            f"""SELECT order_id, user_id, order_type, amount_usd, payment_status,
                       payment_method, created_at, description
                FROM orders
                WHERE user_id = ? AND payment_status IN ({placeholders})
                ORDER BY created_at DESC""",
            (user_id, *SELLABLE_STATUSES),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if close:
            conn.close()


def transfer_order(
    order_id: str,
    source_user_id: str,
    target_email: str,
    price: float | None = None,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """
    Transfer ownership of an order from source_user_id to the user identified by target_email.

    If *price* is provided (and > 0), the target user's wallet is debited and
    the source user's wallet is credited. Otherwise the transfer is a gift (free).

    Returns a dict with keys: success, message, transfer_id, order_id, source, target, price.
    """
    close = conn is None
    if conn is None:
        conn = _get_conn()
    try:
        # 1. Validate source owns the order
        order = get_order(order_id, conn=conn)
        if not order:
            return {"success": False, "message": f"Order {order_id} not found."}
        if order["user_id"] != source_user_id:
            return {
                "success": False,
                "message": "You do not own this order.",
            }
        if order["payment_status"] not in SELLABLE_STATUSES:
            return {
                "success": False,
                "message": f"Order status '{order['payment_status']}' is not sellable. "
                f"Allowed: {', '.join(sorted(SELLABLE_STATUSES))}.",
            }

        # 2. Validate target user exists
        target = get_user_by_email(target_email, conn=conn)
        if not target:
            return {"success": False, "message": f"No user found with email '{target_email}'."}
        if target["user_id"] == source_user_id:
            return {"success": False, "message": "Cannot transfer an order to yourself."}

        target_user_id: str = target["user_id"]

        # 3. Check target wallet balance if price > 0
        price = abs(price) if price is not None else 0.0
        if price > 0 and (target.get("wallet_balance", 0) or 0) < price:
            return {
                "success": False,
                "message": f"Target user has insufficient wallet balance "
                f"({target.get('wallet_balance', 0):.2f} < {price:.2f}).",
            }

        # 4. Execute transfer atomically
        transfer_id = f"TRF-{uuid.uuid4().hex[:12].upper()}"
        now_iso = datetime.now(UTC).isoformat()

        try:
            conn.execute("BEGIN IMMEDIATE")

            # 4a. Update order ownership
            conn.execute(
                "UPDATE orders SET user_id = ?, updated_at = ? WHERE order_id = ?",
                (target_user_id, now_iso, order_id),
            )

            # 4b. Wallet transfers
            if price > 0:
                # Debit target
                conn.execute(
                    """INSERT INTO wallet_transactions
                       (user_id, amount, txn_type, description, created_at)
                       VALUES (?, ?, 'deduction', ?, ?)""",
                    (target_user_id, -price, f"Purchase of order {order_id} (transfer {transfer_id})", now_iso),
                )
                conn.execute(
                    "UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ?",
                    (price, target_user_id),
                )

                # Credit source
                conn.execute(
                    """INSERT INTO wallet_transactions
                       (user_id, amount, txn_type, description, created_at)
                       VALUES (?, ?, 'deposit', ?, ?)""",
                    (source_user_id, price, f"Sale of order {order_id} (transfer {transfer_id})", now_iso),
                )
                conn.execute(
                    "UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?",
                    (price, source_user_id),
                )

            # 4c. Log the transfer
            conn.execute(
                """INSERT INTO order_transfers
                   (transfer_id, order_id, source_user_id, target_user_id,
                    price, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 'completed', ?)""",
                (transfer_id, order_id, source_user_id, target_user_id, price, now_iso),
            )

            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("Transfer failed, rolled back.")
            return {"success": False, "message": "Database error during transfer. Transaction rolled back."}

        return {
            "success": True,
            "message": f"Order {order_id} transferred successfully to {target_email}."
            if price == 0
            else f"Order {order_id} sold to {target_email} for ${price:.2f}.",
            "transfer_id": transfer_id,
            "order_id": order_id,
            "source_user_id": source_user_id,
            "target_user_id": target_user_id,
            "price": price,
        }

    finally:
        if close:
            conn.close()


def ensure_transfer_table(conn: sqlite3.Connection | None = None):
    """Create the order_transfers table if it doesn't exist."""
    close = conn is None
    if conn is None:
        conn = _get_conn()
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS order_transfers (
                transfer_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                source_user_id TEXT NOT NULL,
                target_user_id TEXT NOT NULL,
                price REAL DEFAULT 0,
                status TEXT DEFAULT 'completed',
                created_at TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )"""
        )
        conn.commit()
    finally:
        if close:
            conn.close()


# ── CLI ─────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Service Subscription Sell/Transfer Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # transfer
    t = sub.add_parser("transfer", help="Transfer/sell an order to another user")
    t.add_argument("--order-id", required=True, help="Order ID to transfer")
    t.add_argument("--source-user", required=True, help="Current owner's user_id")
    t.add_argument("--target-email", required=True, help="Recipient's email address")
    t.add_argument("--price", type=float, default=None, help="Sale price (omit for free transfer)")

    # list
    l = sub.add_parser("list", help="List sellable orders for a user")
    l.add_argument("--user-id", required=True, help="User ID to list orders for")

    # info
    i = sub.add_parser("info", help="Show order details")
    i.add_argument("--order-id", required=True, help="Order ID to inspect")

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    ensure_transfer_table()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "transfer":
        result = transfer_order(
            order_id=args.order_id,
            source_user_id=args.source_user,
            target_email=args.target_email,
            price=args.price,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("success") else 1

    elif args.command == "list":
        orders = list_orders_for_user(args.user_id)
        if not orders:
            print(json.dumps({"orders": [], "message": "No sellable orders found."}, indent=2))
            return 0
        print(json.dumps({"orders": orders, "count": len(orders)}, indent=2, ensure_ascii=False, default=str))
        return 0

    elif args.command == "info":
        order = get_order(args.order_id)
        if not order:
            print(json.dumps({"error": f"Order {args.order_id} not found."}, indent=2))
            return 1
        print(json.dumps(order, indent=2, ensure_ascii=False, default=str))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
