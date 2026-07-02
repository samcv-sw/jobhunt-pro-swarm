"""
GENESIS PROTOCOL: TALENT STOCK EXCHANGE
=======================================
Generates a Binance-style B2B "Human IPO" Dashboard.
Turns developers into "Investable Digital Assets".
"""

import sqlite3
import os
import random
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] EXCHANGE-GEN: %(message)s"
)
logger = logging.getLogger(__name__)

# Resolved relative to project root
from pathlib import Path

try:
    import config

    db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
except ImportError:
    db_name = "jobhunt_saas_v2.db"
DB_PATH = str(Path(__file__).resolve().parent.parent / db_name)
OUTPUT_HTML = "exchange.html"
B2B_ACQUIRE_LINK = "https://t.me/JobHuntProBot?start=acquire_asset"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talent Stock Exchange | Human IPOs</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
        body {{
            margin: 0;
            padding: 0;
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: 'Roboto Mono', monospace;
        }}
        header {{
            background: #161b22;
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid #30363d;
        }}
        h1 {{
            margin: 0;
            color: #58a6ff;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .ticker-tape {{
            background: #000;
            color: #3fb950;
            padding: 10px;
            white-space: nowrap;
            overflow: hidden;
            box-sizing: border-box;
            font-weight: bold;
        }}
        .ticker-tape p {{
            display: inline-block;
            padding-left: 100%;
            animation: ticker 15s linear infinite;
            margin: 0;
        }}
        @keyframes ticker {{
            0% {{ transform: translate(0, 0); }}
            100% {{ transform: translate(-100%, 0); }}
        }}
        .exchange-container {{
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #161b22;
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #30363d;
        }}
        th {{
            background: #21262d;
            color: #8b949e;
            text-transform: uppercase;
            font-size: 0.85em;
        }}
        tr:hover {{
            background: #1f2428;
        }}
        .symbol {{
            color: #fff;
            font-weight: bold;
            font-size: 1.1em;
        }}
        .positive-trend {{ color: #3fb950; }}
        .negative-trend {{ color: #f85149; }}
        .btn-acquire {{
            background: #238636;
            color: #fff;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            transition: background 0.3s;
        }}
        .btn-acquire:hover {{
            background: #2ea043;
        }}
        .altruism-banner {{
            background: #1f6feb;
            color: #fff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Talent Stock Exchange</h1>
        <p>The World's First Decentralized Human IPO Platform</p>
    </header>
    
    <div class="ticker-tape">
        <p>MARKET UPDATE: HR Teams from Google, Stripe, and Meta are currently acquiring top assets. Act fast to secure top 1% global talent. 50% of the Acquisition Fee is instantly wired to the candidate as a signing bonus.</p>
    </div>

    <div class="exchange-container">
        <div class="altruism-banner">
            <strong>🌍 The Altruism Guarantee:</strong> When you acquire an asset for $500, $250 is instantly transferred to the developer in their local currency as an upfront signing bonus. You get elite talent, they get immediate financial empowerment.
        </div>

        <table>
            <thead>
                <tr>
                    <th>Asset Symbol</th>
                    <th>Tech Stack Focus</th>
                    <th>Market Value</th>
                    <th>24h Momentum</th>
                    <th>AI Clone Interviews</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {TABLE_ROWS}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

ROW_TEMPLATE = """
<tr>
    <td><span class="symbol">{symbol}</span></td>
    <td>{skills}</td>
    <td>${value}</td>
    <td class="{trend_class}">{trend}</td>
    <td>{interviews}</td>
    <td><a href="{B2B_ACQUIRE_LINK}?asset={symbol}" class="btn-acquire" target="_blank">ACQUIRE</a></td>
</tr>
"""


def generate_stock_exchange():
    """Generates the exchange.html dashboard."""
    logger.info("Initializing Genesis Protocol: Talent Stock Exchange Generator...")

    assets = []

    # Try to fetch from DB, fallback to mock if DB empty
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT id, name, skills FROM users LIMIT 15")
            rows = cur.fetchall()

            for row in rows:
                skill_list = (
                    row["skills"].split(",") if row["skills"] else ["Python", "JS"]
                )
                assets.append(
                    {
                        "id": row["id"],
                        "skills": ", ".join(skill_list[:3]),
                        "country": random.choice(
                            ["IND", "BRA", "NGA", "PHL", "EGY", "MEX"]
                        ),
                    }
                )
            conn.close()
        except Exception as e:
            logger.error(f"DB Error: {e}")

    # Mock data if not enough assets
    if len(assets) < 5:
        mock_countries = ["IND", "BRA", "NGA", "PHL", "EGY", "MEX"]
        mock_skills = [
            ("React", "Node.js"),
            ("Python", "Django"),
            ("Go", "Docker"),
            ("Rust", "WASM"),
            ("Java", "Spring"),
        ]
        for i in range(10):
            assets.append(
                {
                    "id": random.randint(1000, 9999),
                    "skills": ", ".join(random.choice(mock_skills)),
                    "country": random.choice(mock_countries),
                }
            )

    rows_html = ""
    for asset in assets:
        symbol = f"ENG-{asset['country']}-{asset['id']}"
        value = 500  # Standard B2B acquisition fee

        # Simulate stock market metrics
        momentum = round(random.uniform(-5.0, 25.0), 2)
        trend_class = "positive-trend" if momentum >= 0 else "negative-trend"
        trend_str = f"▲ +{momentum}%" if momentum >= 0 else f"▼ {momentum}%"

        interviews = random.randint(3, 42)

        row = ROW_TEMPLATE.format(
            symbol=symbol,
            skills=asset["skills"],
            value=value,
            trend_class=trend_class,
            trend=trend_str,
            interviews=interviews,
            B2B_ACQUIRE_LINK=B2B_ACQUIRE_LINK,
        )
        rows_html += row

    final_html = HTML_TEMPLATE.replace("{TABLE_ROWS}", rows_html)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(final_html)

    logger.info(f"Successfully generated {OUTPUT_HTML}")
    return True


if __name__ == "__main__":
    generate_stock_exchange()
