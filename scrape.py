from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Set up Chrome with your logged-in user profile
chrome_profile_path = r"C:\Users\mmaka\AppData\Local\Google\Chrome\User Data"
profile_dir = "Default"  # or "Profile 1" if that was your custom one

options = Options()
options.add_argument(f"user-data-dir={chrome_profile_path}")
options.add_argument(f"profile-directory={profile_dir}")
options.add_experimental_option("detach", True)  # keeps the window open

# Launch Chrome
driver = webdriver.Chrome(options=options)

# Go directly to the protected page (since you're already logged in)
driver.get("https://darkhorseodds.com/arbitrage")
time.sleep(5)  # Wait for content to load

# Parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'lxml')

# Find all profit <td> cells
profit_cells = soup.find_all('td', class_='profit-col')

# Print results
print(f"✅ Found {len(profit_cells)} profit entries:")
for cell in profit_cells:
    texts = list(cell.stripped_strings)
    if len(texts) >= 2:
        amount = texts[0]
        percentage = texts[1]
        print(f"- 💵 {amount} | 📈 {percentage}")
    else:
        print(f"- ⚠️ Unexpected format: {texts}")

# Optional: driver.quit()
