import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
from datetime import timezone, datetime
import time
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# --- Load secrets from .env ---
load_dotenv()
USER_KEY = os.getenv("USER_KEY") 
APP_TOKEN = os.getenv("APP_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# --- Pushover setup ---
def send_push_notification(user_key, app_token, message, title="DarkHorse Alert"):
    payload = {
        "token": app_token,
        "user": user_key,
        "message": message,
        "title": title
    }
    response = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    return response.status_code == 200

# --- MongoDB setup ---
client = MongoClient(MONGO_URI)
db = client["darkhorse_data"]
collection = db["opportunities"] # Make sure to enter desired database cluster

# Optional: ensure fast duplicate checks
# collection.create_index("entry_hash", unique=True)

# --- Config ---
INTERVAL_MINUTES = 1
MIN_PROFIT_DOLLARS = 12.00
MIN_PERCENT = 2.00

# --- Chrome setup ---
chrome_profile_path = r"C:\Users\mmaka\AppData\Local\Google\Chrome\User Data"
profile_dir = "Profile 2"

options = Options()
options.add_argument(f"user-data-dir={chrome_profile_path}")
options.add_argument(f"profile-directory={profile_dir}")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--log-level=3")

# Launch Chrome once
driver = webdriver.Chrome(options=options)
driver.get("https://darkhorseodds.com/arbitrage")
time.sleep(5)

# --- Scrape and notify ---
def fetch_and_check_arbitrage():
    global driver

    driver.refresh()
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    profit_cells = soup.find_all('td', class_='profit-col')
    new_found = 0

    for cell in profit_cells:
        texts = list(cell.stripped_strings)
        if len(texts) >= 2:
            amount_text = texts[0].replace("$", "").strip()
            percent_text = texts[1].replace("%", "").strip()

            try:
                amount = float(amount_text)
                percent = float(percent_text)
            except ValueError:
                print(f"⚠️ Skipping invalid entry: {texts}")
                continue

            if amount > MIN_PROFIT_DOLLARS or percent > MIN_PERCENT:
                # 🧩 Get full row
                row = cell.find_parent("tr")

                # 🕒 Extract event time
                time_cell = row.find("td", class_="time-col")
                if time_cell:
                    time_parts = list(time_cell.stripped_strings)
                    event_time = " ".join(time_parts)
                else:
                    event_time = "Unknown"

                # 🏦 Extract sportsbook names
                bookmakers = row.find_all("img", alt=True)
                sportsbook_1 = bookmakers[0]["alt"] if len(bookmakers) >= 1 else "Unknown"
                sportsbook_2 = bookmakers[1]["alt"] if len(bookmakers) >= 2 else "Unknown"

                # 🔐 Generate entry hash
                identifier = f"{sportsbook_1}_{sportsbook_2}_{event_time}_{amount:.2f}_{percent:.2f}"
                entry_hash = hashlib.md5(identifier.encode()).hexdigest()

                # ❌ Skip if already in MongoDB
                if collection.find_one({"entry_hash": entry_hash}):
                    continue

                # 📢 Log
                print(f"🔔 New: ${amount:.2f} | {percent:.2f}%")
                print(f"📆 Event Time: {event_time}")
                print(f"🏦 Books: {sportsbook_1} vs {sportsbook_2}")

                # 📲 Push notification
                send_push_notification(
                    USER_KEY,
                    APP_TOKEN,
                    f"{sportsbook_1} vs {sportsbook_2}\n{event_time}\n${amount:.2f} | {percent:.2f}%"
                )

                # 💾 Save to MongoDB
                collection.insert_one({
                    "time_posted": datetime.now(timezone.utc),
                    "sportsbook_1": sportsbook_1,
                    "sportsbook_2": sportsbook_2,
                    "event_time": event_time,
                    "profit_percent": percent,
                    "profit_dollars": amount,
                    "entry_hash": entry_hash
                })
                print("   Saved to MongoDB\n")

                new_found += 1

    if new_found == 0:
        print("✅ No new qualifying entries.")
    else:
        print(f"📬 Sent {new_found} new notification(s).")

# --- Main loop ---
print(f"📡 Monitoring every {INTERVAL_MINUTES} min | Thresholds: > ${MIN_PROFIT_DOLLARS} or > {MIN_PERCENT}%\n")

try:
    while True:
        fetch_and_check_arbitrage()
        print(f"🕒 Sleeping {INTERVAL_MINUTES} minutes...\n")
        time.sleep(INTERVAL_MINUTES * 60)
except KeyboardInterrupt:
    print("🛑 Script manually stopped.")
    driver.quit()
