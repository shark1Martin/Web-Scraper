from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import time

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

# --- Config ---
INTERVAL_MINUTES = 5
MIN_PROFIT_DOLLARS = 10.00
MIN_PERCENT = 2.00

# --- Chrome setup (headless) ---
chrome_profile_path = r"C:\Users\mmaka\AppData\Local\Google\Chrome\User Data"
profile_dir = "Default"

options = Options()
options.add_argument(f"user-data-dir={chrome_profile_path}")
options.add_argument(f"profile-directory={profile_dir}")
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--log-level=3")

# Cache of already-notified entries
seen_entries = set()

def fetch_and_check_arbitrage():
    global seen_entries

    driver = webdriver.Chrome(options=options)
    driver.get("https://darkhorseodds.com/arbitrage")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.quit()

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

                # Only send if not already seen
                if entry not in seen_entries:
                    print(f"🔔 New: {entry}")
                    send_push_notification(USER_KEY, APP_TOKEN, f"New Opportunity:\n{entry}")
                    seen_entries.add(entry)
                    new_found += 1

    if new_found == 0:
        print("✅ No new qualifying entries.")
    else:
        print(f"📬 Sent {new_found} new notification(s).")

# --- Loop forever ---
print(f"📡 Monitoring started. Every {INTERVAL_MINUTES} min | Thresholds: > ${MIN_PROFIT_DOLLARS} or > {MIN_PERCENT}%")

try:
    while True:
        fetch_and_check_arbitrage()
        print(f"🕒 Sleeping {INTERVAL_MINUTES} minutes...\n")
        time.sleep(INTERVAL_MINUTES * 60)
except KeyboardInterrupt:
    print("🛑 Script manually stopped.")
