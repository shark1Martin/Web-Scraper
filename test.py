from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument(r"user-data-dir=C:\Users\mmaka\AppData\Local\Google\Chrome\User Data")
options.add_argument("profile-directory=Profile 1")  # or Profile 2
options.add_argument("--headless=chrome")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
driver.get("https://darkhorseodds.com/arbitrage")
print(driver.title)
driver.quit()
