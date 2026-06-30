#!/usr/bin/env python3
"""
JobHunt Pro -- SELLING TOOL v1.0
=================================
Interactive CLI to sell services ($2-$20) and process crypto payments.
Run: python sell.py

Commands:
  catalog     - Show all services with prices
  sell        - Start interactive selling flow
  orders      - View all orders and payment status
  confirm     - Confirm payment for an order
  stats       - Show sales statistics
  deliver     - Manually trigger delivery for paid orders
  addresses   - Show your crypto wallet addresses
  report      - Generate sales report
  auto        - Start auto-selling mode (monitors for payments)
  help        - Show this help
"""
import asyncio
import sys
import os

# Fix Windows console encoding so UTF-8 chars display properly
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"
import json
import os
import sys
from datetime import datetime

import config

# ── IMPORT SERVICES ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.catalog import (
    SERVICE_CATALOG, BOUQUET_CATALOG, format_catalog_markdown,
    get_service, get_bouquet,
)
from services.fulfillment import ServiceFulfillment
from payments import record_payment, get_payment_addresses, get_payment_stats


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print("=" * 65)
    print("  🔥  JOBHUNT PRO — SELLING ENGINE v1.0  🔥")
    print("  Automated Service Delivery & Crypto Payments")
    print("=" * 65)


def print_menu():
    print()
    print("  📋  COMMANDS:")
    print("  ─────────────────────────────────────────────")
    print("  1. catalog    — Show all services ($2-$20)")
    print("  2. sell       — Start selling flow")
    print("  3. orders     — View all orders")
    print("  4. confirm    — Confirm payment for order")
    print("  5. stats      — Sales & revenue statistics")
    print("  6. deliver    — Deliver paid orders")
    print("  7. addresses  — Show wallet addresses")
    print("  8. report     — Generate sales report")
    print("  9. auto       — Auto-selling mode (monitor)")
    print("  10. help      — Detailed help")
    print("  0. exit       — Exit")
    print("  ─────────────────────────────────────────────")


def cmd_catalog():
    """Show full service catalog."""
    clear()
    print_banner()
    print("\n⚠️  COPY THIS AND SEND TO CUSTOMERS:\n")
    print(format_catalog_markdown())
    input("\n\nPress Enter to return...")


def cmd_sell():
    """Interactive selling flow."""
    fulfillment = ServiceFulfillment()

    clear()
    print_banner()
    print("\n💼  INTERACTIVE SELLING FLOW")
    print("─" * 50)

    # Step 1: Get customer info
    print("\n📝  CUSTOMER INFORMATION:")
    customer_name = input("  Customer name: ").strip()
    customer_email = input("  Customer email: ").strip()
    if not customer_email:
        print("  ❌ Email is required!")
        input("Press Enter...")
        return

    # Step 2: Choose service or bouquet
    print("\n📦  WHAT TO SELL?")
    print("  1. Individual service ($2-$20)")
    print("  2. Bouquet package ($5-$20)")
    choice = input("  Choice (1/2): ").strip()

    if choice == "2":
        # Show bouquets
        print("\n🎁  BOUQUET PACKAGES:")
        for i, b in enumerate(BOUQUET_CATALOG, 1):
            print(f"  {i}. {b['name']} — ${b['price']} (Save {b['savings']})")
            print(f"     Includes: {', '.join(s['name'] for s in SERVICE_CATALOG if s['id'] in b['services'])}")
        try:
            b_idx = int(input("\n  Choose bouquet (number): ")) - 1
            bouquet = BOUQUET_CATALOG[b_idx]
        except (ValueError, IndexError):
            print("  ❌ Invalid choice!")
            input("Press Enter...")
            return

        order = fulfillment.create_order(
            service_id=bouquet["id"],
            customer_email=customer_email,
            customer_name=customer_name,
            is_bouquet=True,
        )
    else:
        # Show services by price range
        print("\n💰  PRICE RANGE:")
        print("  1. $2-$5 (Micro services)")
        print("  2. $6-$10 (Standard services)")
        print("  3. $12-$20 (Premium services)")
        print("  4. All services")
        try:
            pr_choice = int(input("  Choose (1-4): "))
            ranges = {1: (2, 5), 2: (6, 10), 3: (12, 20), 4: (2, 20)}
            min_p, max_p = ranges.get(pr_choice, (2, 20))
        except ValueError:
            min_p, max_p = 2, 20

        services = [s for s in SERVICE_CATALOG if min_p <= s["price"] <= max_p]
        print(f"\n📦  SERVICES (${min_p}-${max_p}):")
        for i, s in enumerate(services, 1):
            print(f"  {i}. {s['name']} — ${s['price']}")
            print(f"     {s['description'][:80]}...")
        try:
            s_idx = int(input("\n  Choose service (number): ")) - 1
            service = services[s_idx]
        except (ValueError, IndexError):
            print("  ❌ Invalid choice!")
            input("Press Enter...")
            return

        order = fulfillment.create_order(
            service_id=service["id"],
            customer_email=customer_email,
            customer_name=customer_name,
        )

    if "error" in order:
        print(f"\n  ❌ Error: {order['error']}")
        input("Press Enter...")
        return

    # Step 3: Show payment details
    clear()
    print_banner()
    print("\n✅  ORDER CREATED SUCCESSFULLY!")
    print("─" * 50)
    print(f"\n  Order ID:     {order['order_id']}")
    print(f"  Service:      {order['service_name']}")
    print(f"  Price:        ${order['price']}")
    print(f"  Customer:     {customer_name} <{customer_email}>")
    print(f"  Status:       ⏳ Awaiting Payment")

    # Show payment_code if present
    payment_code = order.get("payment_code", "")
    if payment_code:
        print(f"\n  🔑 PAYMENT CODE: {payment_code}")
        print(f"     (Customer MUST provide this code to confirm payment)")

    print(f"\n{'='*60}")
    print(f"  📤  SEND THIS TO THE CUSTOMER:")
    print(f"{'='*60}")
    print(f"\n  Hi {customer_name},")
    print(f"\n  Thank you for your interest in **{order['service_name']}**!")
    print(f"\n  Your order ID: **{order['order_id']}**")
    print(f"  Total: **${order['price']}**")
    print(f"\n  🔑 Your Payment Code: **{payment_code}**")
    print(f"  (Keep this code — you'll need it to confirm your payment)")
    print(f"\n  Please send payment to one of the following addresses:")
    for currency, addr in order["crypto_addresses"].items():
        if addr:
            print(f"\n  💳 {currency}: {addr}")
    print(f"\n  After sending payment, reply with the transaction hash")
    print(f"  AND your payment code to receive your service!")
    print(f"\n  ⚡ Delivery: {order.get('delivery_method', 'email')}")
    print(f"{'='*60}")

    # Log the sale
    with open("cache/sales_log.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(
            f"[{timestamp}] SOLD: {order['service_name']} | "
            f"${order['price']} | {customer_email} | "
            f"Order: {order['order_id']}\n"
        )

    print(f"\n  💾 Sale logged to cache/sales_log.txt")
    input("\n  Press Enter to return...")


def cmd_orders():
    """View all orders."""
    fulfillment = ServiceFulfillment()
    stats = fulfillment.get_stats()

    clear()
    print_banner()
    print("\n📋  ALL ORDERS")
    print("─" * 50)
    print(f"\n  Total Orders: {stats['total_orders']}")
    print(f"  Total Revenue: ${stats['total_revenue']:.2f}")
    print(f"  Pending Payment: {stats['pending_payment']}")
    print(f"  Paid (to deliver): {stats['paid']}")
    print(f"  Delivered: {stats['delivered']}")
    print(f"  Failed: {stats['failed']}")
    print()

    orders = fulfillment._orders.get("orders", [])
    if not orders:
        print("  No orders yet.")
    else:
        for o in orders:
            status_icon = {
                "pending_payment": "⏳",
                "paid": "✅",
                "delivered": "📬",
                "delivery_failed": "❌",
            }.get(o["status"], "❓")
            print(
                f"  {status_icon} {o['order_id']} | "
                f"{o['service_name']} | ${o['price']} | "
                f"{o['customer_email']} | {o['status']}"
            )
            if o.get("tx_hash"):
                print(f"     TX: {o['tx_hash']}")

    input("\nPress Enter to return...")


def cmd_confirm():
    """Confirm payment for an order and trigger delivery."""
    fulfillment = ServiceFulfillment()
    pending = fulfillment.get_pending_orders()

    clear()
    print_banner()
    print("\n✅  CONFIRM PAYMENT")
    print("─" * 50)

    if not pending:
        print("\n  No pending orders.")
        input("Press Enter...")
        return

    print("\n  ⏳ ORDERS AWAITING PAYMENT:")
    for i, o in enumerate(pending, 1):
        pc = o.get("payment_code", "N/A")
        print(f"  {i}. {o['order_id']} — {o['service_name']} — ${o['price']}")
        print(f"     Customer: {o['customer_email']}  |  Code: {pc}")

    try:
        idx = int(input("\n  Select order to confirm (number): ")) - 1
        order = pending[idx]
    except (ValueError, IndexError):
        print("  ❌ Invalid choice!")
        input("Press Enter...")
        return

    print(f"\n  Order: {order['order_id']}")
    print(f"  Payment Code on record: {order.get('payment_code', 'N/A')}")
    customer_code = input("  Customer's payment code: ").strip()
    tx_hash = input("  Transaction hash (or press Enter for manual): ").strip()

    # Verify payment code matches
    stored_code = order.get("payment_code", "")
    if not stored_code:
        print("  ⚠️  No payment code on record — skipping verification")
    elif customer_code != stored_code:
        print(f"\n  ❌ Payment code mismatch! Expected '{stored_code}', got '{customer_code}'")
        print("  Ask the customer for their correct payment code.")
        input("Press Enter...")
        return

    # Record payment (pass payment_code + client_ip for audit)
    record_payment(
        order_id=order["order_id"],
        currency="USDT",
        amount_usd=order["price"],
        tx_hash=tx_hash or "manual",
        customer_email=order["customer_email"],
        payment_code="ADMIN_INTERNAL",
        client_ip="sell.py",
    )

    print(f"\n  ✅ Payment confirmed! Service will be delivered to {order['customer_email']}")
    input("Press Enter...")


def cmd_stats():
    """Show sales statistics."""
    fulfillment = ServiceFulfillment()
    stats = fulfillment.get_stats()
    payment_stats = get_payment_stats()

    clear()
    print_banner()
    print("\n📊  SALES & REVENUE STATISTICS")
    print("─" * 50)
    print(f"\n  💰 Total Revenue:     ${stats['total_revenue']:.2f}")
    print(f"  📦 Total Orders:      {stats['total_orders']}")
    print(f"  ⏳ Pending Payment:   {stats['pending_payment']}")
    print(f"  ✅ Paid (to deliver): {stats['paid']}")
    print(f"  📬 Delivered:         {stats['delivered']}")
    print(f"  ❌ Failed:            {stats['failed']}")

    print(f"\n  💳 Payment Stats:")
    print(f"     Total Received: ${payment_stats['total_received_usd']:.2f}")
    print(f"     Total Payments: {payment_stats['total_payments']}")
    if payment_stats.get("by_currency"):
        for cur, amt in payment_stats["by_currency"].items():
            print(f"     {cur}: ${amt:.2f}")

    input("\nPress Enter to return...")


def cmd_deliver():
    """Manually trigger delivery for paid orders."""
    fulfillment = ServiceFulfillment()
    paid = fulfillment.get_paid_orders()

    clear()
    print_banner()
    print("\n📬  MANUAL DELIVERY")
    print("─" * 50)

    if not paid:
        print("\n  No paid orders awaiting delivery.")
        input("Press Enter...")
        return

    print(f"\n  Found {len(paid)} paid orders to deliver:")
    for i, o in enumerate(paid, 1):
        print(f"  {i}. {o['order_id']} — {o['service_name']} → {o['customer_email']}")

    confirm = input("\n  Deliver all now? (y/n): ").strip().lower()
    if confirm == "y":
        print("\n  🚀 Delivering...")
        for o in paid:
            result = asyncio.run(fulfillment.deliver_service(o["order_id"]))
            status = "✅" if result else "❌"
            print(f"  {status} {o['service_name']} → {o['customer_email']}")
        print("\n  ✅ All deliveries complete!")
    else:
        print("  Cancelled.")

    input("Press Enter...")


def cmd_addresses():
    """Show wallet addresses."""
    addrs = get_payment_addresses()

    clear()
    print_banner()
    print("\n💳  YOUR CRYPTO WALLET ADDRESSES")
    print("─" * 50)
    print("\n  Share these with customers for payment:")
    for currency, addr in addrs.items():
        if addr:
            print(f"\n  {currency}:")
            print(f"  {addr}")
        else:
            print(f"\n  {currency}: ❌ Not configured (add to .env)")

    print(f"\n\n  📝 Configure in .env file:")
    print(f"     CRYPTO_BTC_ADDRESS=...")
    print(f"     CRYPTO_ETH_ADDRESS=...")
    print(f"     CRYPTO_USDT_ADDRESS=...")
    print(f"     CRYPTO_LTC_ADDRESS=...")

    input("\nPress Enter to return...")


def cmd_report():
    """Generate a sales report file."""
    fulfillment = ServiceFulfillment()
    stats = fulfillment.get_stats()
    payment_stats = get_payment_stats()

    report = []
    report.append("=" * 60)
    report.append("  JOBHUNT PRO — SALES REPORT")
    report.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)
    report.append("")
    report.append(f"  TOTAL REVENUE:    ${stats['total_revenue']:.2f}")
    report.append(f"  TOTAL ORDERS:     {stats['total_orders']}")
    report.append(f"  DELIVERED:        {stats['delivered']}")
    report.append(f"  PENDING PAYMENT:  {stats['pending_payment']}")
    report.append(f"  FAILED:           {stats['failed']}")
    report.append("")
    report.append("  --- RECENT ORDERS ---")
    for o in fulfillment._orders.get("orders", [])[-10:]:
        report.append(
            f"  [{o['status']}] {o['service_name']} — ${o['price']} "
            f"— {o['customer_email']} — {o.get('created_at', '')[:10]}"
        )
    report.append("")
    report.append("  --- PAYMENT STATS ---")
    report.append(f"  Total Received: ${payment_stats['total_received_usd']:.2f}")
    report.append(f"  Total Payments: {payment_stats['total_payments']}")
    report.append("")

    report_text = "\n".join(report)
    print(report_text)

    # Save to file
    os.makedirs("cache", exist_ok=True)
    filename = f"cache/sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n  💾 Report saved to: {filename}")
    input("\nPress Enter to return...")


def cmd_auto():
    """Auto-selling mode — monitors for new orders and payments."""
    clear()
    print_banner()
    print("\n🔄  AUTO-SELLING MODE")
    print("─" * 50)
    print("\n  This mode will:")
    print("  • Monitor for new pending orders")
    print("  • Auto-deliver when payment is confirmed")
    print("  • Log all sales activity")
    print("  • Run every 30 seconds")
    print("\n  Press Ctrl+C to stop.\n")

    fulfillment = ServiceFulfillment()
    try:
        cycle = 0
        while True:
            cycle += 1
            now = datetime.now().strftime("%H:%M:%S")
            stats = fulfillment.get_stats()

            # Check for paid orders to deliver
            paid = fulfillment.get_paid_orders()
            if paid:
                print(f"  [{now}] 🚀 Delivering {len(paid)} paid order(s)...")
                for o in paid:
                    result = asyncio.run(fulfillment.deliver_service(o["order_id"]))
                    icon = "✅" if result else "❌"
                    print(f"     {icon} {o['service_name']} → {o['customer_email']}")

            # Show status
            print(
                f"  [{now}] Cycle {cycle} | "
                f"💰 ${stats['total_revenue']:.2f} | "
                f"📦 {stats['total_orders']} orders | "
                f"⏳ {stats['pending_payment']} pending | "
                f"📬 {stats['delivered']} delivered"
            )

            import time
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n  Auto-selling mode stopped.")
        input("Press Enter to return...")


def cmd_help():
    """Show detailed help."""
    clear()
    print_banner()
    print("""
  📖  DETAILED HELP
  ─────────────────────────────────────────────

  catalog     — Shows ALL services ($2-$20) with descriptions.
                Copy-paste this to WhatsApp/Telegram customers.

  sell        — Interactive flow to sell a service:
                1. Enter customer name & email
                2. Choose service or bouquet
                3. Get order ID + crypto address
                4. Send payment details to customer

  orders      — View every order with status:
                ⏳ pending_payment = waiting for crypto
                ✅ paid = payment received, ready to deliver
                📬 delivered = service sent to customer

  confirm     — When customer says they sent payment:
                1. Select the order
                2. Enter transaction hash (optional)
                3. System auto-delivers the service

  stats       — Real-time dashboard of:
                Revenue, orders, delivery status

  deliver     — Manually deliver all paid-but-undelivered orders

  addresses   — Your BTC/ETH/USDT/LTC wallet addresses

  report      — Generates detailed sales report file

  auto        — Background mode: auto-delivers every 30 seconds


  💡  QUICK SELLING WORKFLOW:
  ─────────────────────────────────────────────

  1. python sell.py catalog
     → Copy catalog, send to customer on WhatsApp

  2. python sell.py sell
     → Create order, get crypto address

  3. Customer sends crypto
     → You run: python sell.py confirm
     → System auto-delivers to their email

  4. Check: python sell.py stats
     → See revenue growing

  💰  PROFIT CALCULATOR:
  ─────────────────────────────────────────────

  10 sales/day × $10 avg = $100/day = $3,000/month
  20 sales/day × $15 avg = $300/day = $9,000/month
  50 sales/day × $10 avg = $500/day = $15,000/month

  Plus your own 104+ applications working for you!
    """)
    input("Press Enter to return...")


def main():
    while True:
        clear()
        print_banner()
        print_menu()
        cmd = input("\n  >> Enter command: ").strip().lower()

        commands = {
            "1": cmd_catalog,
            "catalog": cmd_catalog,
            "2": cmd_sell,
            "sell": cmd_sell,
            "3": cmd_orders,
            "orders": cmd_orders,
            "4": cmd_confirm,
            "confirm": cmd_confirm,
            "5": cmd_stats,
            "stats": cmd_stats,
            "6": cmd_deliver,
            "deliver": cmd_deliver,
            "7": cmd_addresses,
            "addresses": cmd_addresses,
            "8": cmd_report,
            "report": cmd_report,
            "9": cmd_auto,
            "auto": cmd_auto,
            "10": cmd_help,
            "help": cmd_help,
            "0": lambda: sys.exit(0),
            "exit": lambda: sys.exit(0),
        }

        command_func = commands.get(cmd)
        if command_func:
            command_func()
        else:
            print(f"\n  [X] Unknown command: {cmd}")
            input("Press Enter...")


if __name__ == "__main__":
    main()
