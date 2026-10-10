"""
Blinkit Stock Monitor
=====================
Searches Blinkit for each item in your WATCHLIST and sends an email
alert when any item comes back in stock. Checks every 2 minutes.

Requirements:
    pip install playwright python-dotenv
    playwright install chromium
"""

import asyncio
import smtplib
import json
import os
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler("blinkit_monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

BLINKIT_URL        = "https://blinkit.com"
CHECK_INTERVAL_SEC = 2 * 60           # 2 minutes

# Gmail credentials (set in .env file)
GMAIL_SENDER   = os.getenv("GMAIL_SENDER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL")

# Session file
SESSION_FILE = "blinkit_session.json"

# ── YOUR WATCHLIST ────────────────────────────────────────────────────────────
WATCHLIST = [
    "Hot Wheels 2020 Ford Mustang Shelby GT500 Die Cast Car",
    "Hot Wheels Formula 1 Scuderia Ferrari HP Die Cast Car",
    "Hot Wheels Porsche 911 Carrera Die Cast Car",
    "Fablue Panda Bamboo Stuffed Plush Toy",
    "Nissin Geki Carbonara Creamy Veg Korean Ramen",
    "Hersheys Kisses Almonds Milk Chocolate Pack",
]

# ── Email ─────────────────────────────────────────────────────────────────────
def send_email(subject: str, html_body: str) -> None:
    if not all([GMAIL_SENDER, GMAIL_PASSWORD, NOTIFY_EMAIL]):
        log.error("Email credentials missing – check your .env file.")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_SENDER, NOTIFY_EMAIL, msg.as_string())
        log.info(f"Email sent to {NOTIFY_EMAIL}")
    except Exception as e:
        log.error(f"Email failed: {e}")


def build_email_html(items: list[dict]) -> str:
    rows = ""
    for item in items:
        rows += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #f0f0f0;">
            <strong style="color:#1a1a1a;">{item['name']}</strong>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f0f0f0;
                     color:#00a651;font-weight:bold;">
            {item.get('price','—')}
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f0f0f0;text-align:center;">
            <a href="{item.get('url', BLINKIT_URL)}"
               style="background:#f7c200;color:#1a1a1a;padding:6px 14px;border-radius:6px;
                      text-decoration:none;font-weight:bold;font-size:13px;">
              Buy Now
            </a>
          </td>
        </tr>"""
    return f"""
    <html><body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f9f9f9;">
      <div style="max-width:560px;margin:32px auto;background:#fff;border-radius:12px;
                  box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;">
        <div style="background:#f7c200;padding:24px 32px;">
          <h1 style="margin:0;color:#1a1a1a;font-size:22px;">Blinkit Stock Alert!</h1>
          <p style="margin:4px 0 0;color:#333;font-size:14px;">
            {len(items)} item(s) are back in stock right now!
          </p>
        </div>
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#fafafa;">
              <th style="padding:10px 16px;text-align:left;font-size:12px;color:#888;
                         text-transform:uppercase;">Item</th>
              <th style="padding:10px 16px;text-align:left;font-size:12px;color:#888;
                         text-transform:uppercase;">Price</th>
              <th style="padding:10px 16px;text-align:center;font-size:12px;color:#888;
                         text-transform:uppercase;">Action</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        <div style="padding:20px 32px;color:#999;font-size:12px;border-top:1px solid #f0f0f0;">
          Checked at {datetime.now().strftime("%d %b %Y, %I:%M %p")} · Blinkit Stock Monitor
        </div>
      </div>
    </body></html>"""


# ── Browser helpers ───────────────────────────────────────────────────────────
async def save_session(context) -> None:
    storage = await context.storage_state()
    with open(SESSION_FILE, "w") as f:
        json.dump(storage, f)
    log.info(f"Session saved -> {SESSION_FILE}")


async def login_manually(playwright) -> None:
    log.info("Opening browser for manual login...")
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page    = await context.new_page()
    await page.goto(BLINKIT_URL)
    print("\n" + "="*60)
    print("  Log in to Blinkit in the browser window that just opened.")
    print("  Once you are fully logged in, come back here and press ENTER.")
    print("="*60 + "\n")
    input("Press ENTER after logging in -> ")
    await save_session(context)
    await browser.close()
    log.info("Login complete. Re-run the script to start monitoring.")


async def search_item(page, item_name: str) -> dict | None:
    try:
        search_url = f"{BLINKIT_URL}/s/?q={item_name.replace(' ', '%20')}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(7000)

        # Save debug screenshot for first run troubleshooting
        await page.screenshot(path=f"debug_search.png")

        # Get full page text to understand structure
        page_text = (await page.inner_text("body")).lower()

        # Try multiple card selectors
        cards = await page.query_selector_all('[data-test-id="product-card"]')
        if not cards:
            cards = await page.query_selector_all('div[class*="ProductCard"]')
        if not cards:
            cards = await page.query_selector_all('div[class*="product-card"]')
        if not cards:
            cards = await page.query_selector_all('a[href*="/prn/"]')
        if not cards:
            cards = await page.query_selector_all('div[class*="Product"]')
        if not cards:
            # Broadest fallback: any small div with a price AND add button
            all_divs = await page.query_selector_all('div')
            cards = []
            for div in all_divs:
                try:
                    txt = (await div.inner_text()).lower()
                    if "₹" in txt and "add" in txt and 10 < len(txt) < 400:
                        cards.append(div)
                except:
                    pass

        log.info(f"  Searching: '{item_name[:35]}' -> {len(cards)} cards found")

        for card in cards:
            card_text = (await card.inner_text()).lower()

            # Must contain key words from the item name (exact match check)
            # Use last 3 meaningful words of item name to match
            name_keywords = [w.lower() for w in item_name.split() if len(w) > 3]
            name_match = sum(1 for kw in name_keywords if kw in card_text)
            is_name_match = name_match >= min(3, len(name_keywords))

            # OUT of stock indicators
            is_oos = any(kw in card_text for kw in [
                "coming soon", "notify me", "out of stock", "currently unavailable"
            ])

            # IN stock indicator — has ADD but none of the OOS keywords
            has_add = "add" in card_text

            if has_add and not is_oos and is_name_match:
                # Extract price
                price = ""
                try:
                    all_text = await card.inner_text()
                    for line in all_text.split("\n"):
                        if "₹" in line:
                            price = line.strip()
                            break
                except:
                    pass

                # Extract URL
                link_el = await card.query_selector("a[href]")
                href = await link_el.get_attribute("href") if link_el else ""
                url = f"{BLINKIT_URL}{href}" if href and href.startswith("/") else BLINKIT_URL

                log.info(f"  ✅ IN STOCK: {item_name[:40]} @ {price}")
                return {"name": item_name, "price": price, "url": url}
            else:
                log.info(f"  ❌ Not available: {item_name[:35]} (oos={is_oos}, add={has_add})")

        log.info(f"  ❌ No matching card: {item_name[:40]}")
        return None

    except PlaywrightTimeout:
        log.warning(f"  Timeout searching for: {item_name}")
        return None
    except Exception as e:
        log.error(f"  Error searching '{item_name}': {e}")
        return None


async def check_all_items(playwright) -> list[dict]:
    if not os.path.exists(SESSION_FILE):
        log.error("No session file found. Run with --login first.")
        return []

    with open(SESSION_FILE) as f:
        storage_state = json.load(f)

    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        storage_state=storage_state,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    page = await context.new_page()
    in_stock = []

    try:
        for item_name in WATCHLIST:
            result = await search_item(page, item_name)
            if result:
                in_stock.append(result)
            await asyncio.sleep(1)
    finally:
        await browser.close()

    return in_stock


# ── Main loop ─────────────────────────────────────────────────────────────────
async def monitor_loop() -> None:
    log.info(f"Blinkit Stock Monitor started. Watching {len(WATCHLIST)} items every 2 minutes.")
    alerted: set[str] = set()

    async with async_playwright() as pw:
        while True:
            log.info("--- Starting stock check ---")
            items = await check_all_items(pw)
            new_items = [i for i in items if i["name"] not in alerted]

            if new_items:
                log.info(f"{len(new_items)} new in-stock item(s)! Sending email...")
                send_email(
                    f"Blinkit: {len(new_items)} item(s) back in stock!",
                    build_email_html(new_items)
                )
                for i in new_items:
                    alerted.add(i["name"])
            else:
                log.info("No new in-stock items. Checking again in 2 minutes.")

            await asyncio.sleep(CHECK_INTERVAL_SEC)


# ── Entry point ───────────────────────────────────────────────────────────────
async def main() -> None:
    import sys
    if "--login" in sys.argv:
        async with async_playwright() as pw:
            await login_manually(pw)
    else:
        if not os.path.exists(SESSION_FILE):
            print("\nNo session found. Run this first:\n")
            print("    python blinkit_monitor.py --login\n")
            return
        await monitor_loop()


if __name__ == "__main__":
    asyncio.run(main())
