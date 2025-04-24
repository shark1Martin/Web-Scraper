from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
from datetime import timezone
import time
import os
from pymongo import MongoClient
from datetime import datetime

# --- Pushover setup ---
USER_KEY = "ubxha8koods5ppmui6r6rjavv1cezo"
APP_TOKEN = "a7enzwkoonfe9u17pbkun7sqfyjogr"

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
MONGO_URI = "mongodb+srv://mmakaveev123:Makaveev2005!@scaper-dev-1.mtjkh66.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["darkhorse_data"]
collection = db["opportunities"]

# --- Config ---
INTERVAL_MINUTES = 1
MIN_PROFIT_DOLLARS = 10.00
MIN_PERCENT = 2.00
NOTIFIED_FILE = "notified_entries.txt"

# --- Chrome setup ---
chrome_profile_path = r"C:\Users\mmaka\AppData\Local\Google\Chrome\User Data"
profile_dir = "Profile 2"

options = Options()
options.add_argument(f"user-data-dir={chrome_profile_path}")
options.add_argument(f"profile-directory={profile_dir}")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--log-level=3")
# options.add_argument("--window-position=10000,10000")  # optional: hide offscreen

# --- Load previously notified entries ---
def load_notified_entries(filepath):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, 'r') as file:
        return set(line.strip() for line in file.readlines())

# --- Save a new entry to the notified file ---
def save_notified_entry(filepath, entry):
    with open(filepath, 'a') as file:
        file.write(entry + '\n')

# Initialize seen entries
seen_entries = load_notified_entries(NOTIFIED_FILE)

# Launch Chrome once
driver = webdriver.Chrome(options=options)
driver.get("https://darkhorseodds.com/arbitrage")
time.sleep(5)

# --- Scrape and notify ---
def fetch_and_check_arbitrage():
    global seen_entries, driver

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
                entry = f"${amount:.2f} | {percent:.2f}%"

                if entry not in seen_entries:
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

                    # 📢 Log everything
                    print(f"🔔 New: {entry}")
                    print(f"📆 Event Time: {event_time}")
                    print(f"🏦 Books: {sportsbook_1} vs {sportsbook_2}")

                    # 🔔 Send notification
                    send_push_notification(
                        USER_KEY,
                        APP_TOKEN,
                        f"{sportsbook_1} vs {sportsbook_2}\n{event_time}\n{entry}"
                    )

                    # 💾 Save to MongoDB
                    collection.insert_one({
                        "time_posted": datetime.now(timezone.utc),
                        "sportsbook_1": sportsbook_1,
                        "sportsbook_2": sportsbook_2,
                        "event_time": event_time,
                        "profit_percent": percent,
                        "profit_dollars": amount
                    })
                    print("   Saved to MongoDB\n")

                    # 🧠 Remember it
                    seen_entries.add(entry)
                    save_notified_entry(NOTIFIED_FILE, entry)
                    new_found += 1

    if new_found == 0:
        print("✅ No new qualifying entries.")
    else:
        print(f"📬 Sent {new_found} new notification(s).")

# --- Main loop ---
print(f"📡 Monitoring every {INTERVAL_MINUTES} min | Thresholds: > ${MIN_PROFIT_DOLLARS} or > {MIN_PERCENT}%")
print(f"🧠 Loaded {len(seen_entries)} remembered entries.\n")

try:
    while True:
        fetch_and_check_arbitrage()
        print(f"🕒 Sleeping {INTERVAL_MINUTES} minutes...\n")
        time.sleep(INTERVAL_MINUTES * 60)
except KeyboardInterrupt:
    print("🛑 Script manually stopped.")
    driver.quit()
