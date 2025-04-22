from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from bs4 import BeautifulSoup
import requests
import time
import os

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
NOTIFIED_FILE = "notified_entries.txt"

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

# --- Click the yellow "Update" button if it exists ---
def click_update_if_available(driver):
    try:
        update_buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in update_buttons:
            classlist = btn.get_attribute("class")
            inner_html = btn.get_attribute("innerHTML").lower()

            if "mat-warn" in classlist and "update" in inner_html:
                btn.click()
                print("🟡 Clicked glowing Update icon button (mat-warn).")
                time.sleep(3)
                return

        print("🔄 No glowing Update button found — reloading page.")
        driver.refresh()
        time.sleep(5)

    except Exception as e:
        print(f"⚠️ Error clicking update button: {e}")
        driver.refresh()
        time.sleep(5)

# Set of entries already notified (persistent across reboots!)
seen_entries = load_notified_entries(NOTIFIED_FILE)

def fetch_and_check_arbitrage():
    global seen_entries

    driver = webdriver.Chrome(options=options)
    driver.get("https://darkhorseodds.com/arbitrage")
    time.sleep(5)

    # NEW: Try to click update, or fallback to reload
    click_update_if_available(driver)

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

                if entry not in seen_entries:
                    print(f"🔔 New: {entry}")
                    send_push_notification(USER_KEY, APP_TOKEN, f"New Opportunity:\n{entry}")
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
