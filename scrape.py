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
opportunities_col = db["entries_V4"]
live_col = db["live_entries"]

# --- Config ---
INTERVAL_MINUTES = 1
MIN_PROFIT_DOLLARS = 12.00
MIN_PERCENT = 2.00

# --- Chrome setup (NOT headless) ---
chrome_profile_path = os.getenv("CHROME_PROFILE_PATH")
profile_dir = "Profile 2"

options = Options()
options.add_argument(f"user-data-dir={chrome_profile_path}")
options.add_argument(f"profile-directory={profile_dir}")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--log-level=3")

# --- Launch Chrome ---
driver = webdriver.Chrome(options=options)
driver.get("https://darkhorseodds.com/arbitrage")
time.sleep(5)

# --- Get thresholds from DB ---
def get_thresholds():
    config = db["config"].find_one({"_id": "thresholds"})
    if config:
        return config.get("min_profit_dollars", MIN_PROFIT_DOLLARS), config.get("min_percent", MIN_PERCENT)
    return MIN_PROFIT_DOLLARS, MIN_PERCENT

# --- Scrape and notify ---
def fetch_and_check_arbitrage():
    global driver

    min_dollars, min_percent = get_thresholds()
    driver.refresh()
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    profit_cells = soup.find_all('td', class_='profit-col')
    new_found = 0

    live_col.delete_many({})  # Clear all live entries

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

            row = cell.find_parent("tr")
            time_cell = row.find("td", class_="time-col")
            event_time = " ".join(list(time_cell.stripped_strings)) if time_cell else "Unknown"

            primary_cell = row.find("td", class_="primary-book-col")
            hedge_cell = row.find("td", class_="hedge-book-col")

            sportsbook_1 = " / ".join(img["alt"] for img in primary_cell.find_all("img", alt=True)) if primary_cell else "Unknown"
            sportsbook_2 = " / ".join(img["alt"] for img in hedge_cell.find_all("img", alt=True)) if hedge_cell else "Unknown"


            identifier = f"{sportsbook_1}_{sportsbook_2}_{event_time}_{amount:.2f}_{percent:.2f}"
            entry_hash = hashlib.md5(identifier.encode()).hexdigest()

            # Save to live_entries regardless of thresholds
            live_col.insert_one({
                "time_posted": datetime.now(timezone.utc),
                "sportsbook_1": sportsbook_1,
                "sportsbook_2": sportsbook_2,
                "event_time": event_time,
                "profit_percent": percent,
                "profit_dollars": amount,
                "entry_hash": entry_hash
            })

            # Notify only if entry is new and passes thresholds
            if amount > min_dollars or percent > min_percent:
                if opportunities_col.find_one({"entry_hash": entry_hash}):
                    continue  # already notified

                print(f"🔔 New: ${amount:.2f} | {percent:.2f}%")
                print(f"📆 Event Time: {event_time}")
                print(f"🏦 Books: {sportsbook_1} vs {sportsbook_2}")

                send_push_notification(
                    USER_KEY,
                    APP_TOKEN,
                    f"{sportsbook_1} vs {sportsbook_2}\n{event_time}\n${amount:.2f} | {percent:.2f}%"
                )

                opportunities_col.insert_one({
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
print(f"Monitoring every {INTERVAL_MINUTES} min | Thresholds: > ${MIN_PROFIT_DOLLARS} or > {MIN_PERCENT}%\n")

try:
    while True:
        fetch_and_check_arbitrage()
        print(f"Sleeping {INTERVAL_MINUTES} minutes...\n")
        time.sleep(INTERVAL_MINUTES * 60)
except KeyboardInterrupt:
    print("🛑 Script manually stopped.")
    driver.quit()
