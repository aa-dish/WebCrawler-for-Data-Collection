import os
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===== Setup download folder =====
download_dir = os.path.join(os.getcwd(), "Downloaded files")
os.makedirs(download_dir, exist_ok=True)

# Chrome options to force PDF download
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # ensures PDFs are downloaded, not opened in Chrome
}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

# Open the base page only once
driver.get("URL")

csv_file = "crawler_test.csv"  # Your CSV file name here

def wait_for_download(folder, timeout=60):
    """Wait for new download to finish (no .crdownload file)"""
    seconds = 0
    while seconds < timeout:
        files = os.listdir(folder)
        if any(f.endswith(".crdownload") for f in files):
            time.sleep(1)
            seconds += 1
        else:
            if files:
                return True
            else:
                time.sleep(1)
                seconds += 1
    return False

def click_element(driver, wait, by, selector):
    el = wait.until(EC.element_to_be_clickable((by, selector)))
    driver.execute_script("arguments[0].scrollIntoView(true);", el)
    time.sleep(0.5)  # small pause to avoid interception issues
    driver.execute_script("arguments[0].click();", el)

def wait_for_popup_to_disappear(driver, timeout=120):
    """Wait for 'Ihre Anfrage wird bearbeitet' modal to disappear"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.XPATH, "//div[contains(text(),'Ihre Anfrage wird bearbeitet')]"))
        )
        print("Processing popup disappeared.")
    except:
        print("Warning: popup did not disappear in time.")

with open(csv_file, newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    # Strip spaces from headers just in case
    reader.fieldnames = [h.strip() for h in reader.fieldnames]

    for i, row in enumerate(reader, 1):
        # Strip spaces from keys to be extra safe
        row = {k.strip(): v for k, v in row.items()}

        art = row['REGI']
        nummer = row['REGIST']
        gericht = row['REGIS']

        print(f"\nProcessing entry {i}: {art} | {nummer} | {gericht}")

      
        print("Clicking Suche...")
        click_element(driver, wait, By.CSS_SELECTOR, "#naviForm\\:Suche > span")

        # Select REGI
        print(f"Selecting REGI: {art}...")
        click_element(driver, wait, By.CSS_SELECTOR, "#form\\:Art .ui-selectonemenu-trigger")
        click_element(driver, wait, By.XPATH, f"//ul[@id='form:Art_items']/li[@data-label='{art}']")

        # Select REGIST
        print(f"Selecting REGIST: {gericht}...")
        click_element(driver, wait, By.CSS_SELECTOR, "#form\\:gericht .ui-selectonemenu-trigger")
        click_element(driver, wait, By.XPATH, f"//ul[@id='form:gericht_items']/li[@data-label='{gericht}']")

        # Enter REGIS
        print(f"Entering REGIS: {nummer}...")
        register_nummer_input = wait.until(EC.presence_of_element_located((By.ID, "form:nummer")))
        register_nummer_input.clear()
        register_nummer_input.send_keys(nummer)

        print("Clicking Find...")
        click_element(driver, wait, By.XPATH, "//*[@id='form:btn']/span")

        # Wait for popup to disappear
        print("Waiting for 'Ihre Anfrage wird bearbeitet' popup to disappear...")
        wait_for_popup_to_disappear(driver, timeout=120)

        # Wait for results
        print("Waiting for results table...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//table[contains(@id,'Form')]//tr")))

        # Click CD link to download PDF
        print("Clicking CD link to download PDF...")
        click_element(driver, wait, By.XPATH, "//a[contains(@onclick,'Global.Dokumentart.PD')]")

        # Wait for download to complete
        print("Waiting for download to complete...")
        if wait_for_download(download_dir, timeout=60):
            print(f"Download completed for entry {i}.")
        else:
            print(f"Download timeout or failure for entry {i}.")

        # Reload main page for next iteration
        print("Reloading main page for next entry...")
        driver.get("URL")
        time.sleep(5)  # buffer time

print("\nAll entries processed.")
input("Press Enter to close browser...")
driver.quit()
