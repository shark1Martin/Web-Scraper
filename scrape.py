from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import time

# --- Pushover setup ---
USER_KEY = "ubxha8koods5ppmui6r6rjavv1cezo"  # Replace with your User Key
APP_TOKEN = "a7enzwkoonfe9u17pbkun7sqfyjogr"  # Replace with your App Token

def send_push_notification(user_key, app_token, message, title="DarkHorse Alert"):
    payload = {
        "token": app_token,
        "user": user_key,
        "message": message,
        "title": title
    }
    response = requests.post("https://api.pushover.net/1/messages.json", data=payload)
    return response.status_code == 200


# --- Chrome setup using your real profile ---
chrome_profile_path = r"C:\Users\mmaka\AppData\Local\Google\Chrome\User Data"
profile_dir = "Default"  # Change if using a different profile

options = Options()
options.add_argument(f"user-data-dir={chrome_profile_path}")
options.add_argument(f"profile-directory={profile_dir}")
options.add_experimental_option("detach", True)  # Keeps Chrome open after script ends

# Launch Chrome browser
driver = webdriver.Chrome(options=options)

# Go directly to the protected page (since you're already logged in)
driver.get("https://darkhorseodds.com/arbitrage")
time.sleep(5)  # Wait for content to load

# Parse the page
soup = BeautifulSoup(driver.page_source, 'lxml')

# Find all profit <td> cells
profit_cells = soup.find_all('td', class_='profit-col')

# Print and send notification
print(f"✅ Found {len(profit_cells)} profit entries:")
for cell in profit_cells:
    texts = list(cell.stripped_strings)
    if len(texts) >= 2:
        amount = texts[0]
        percentage = texts[1]
        message = f"💵 {amount} | 📈 {percentage}"
        print(f"- {message}")
        
        # Send the push notification
        success = send_push_notification(USER_KEY, APP_TOKEN, message)
        if success:
            print("🔔 Notification sent.")
        else:
            print("❌ Failed to send notification.")
    else:
        print(f"- ⚠️ Unexpected format: {texts}")

# Optional: Keep browser open or close it
# driver.quit()
