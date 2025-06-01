# expedia_car_scraper.py
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from time import sleep
import json
import csv

# Format date to Expedia label style
def format_expedia_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%A, %B %-d, %Y") if not date_str.startswith("0") else dt.strftime("%A, %B %#d, %Y")

def load_json_config(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

# Read CSV input
def load_csv_inputs(file_path):
    configs = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            configs.append({
                "pickup_location": row["from"],
                "pickup_label_contains": row["from"],
                "dropoff_location": row["to"],
                "dropoff_label_contains": row["to"],
                "pickup_date": format_expedia_date(row["pickup_date"]),
                "dropoff_date": format_expedia_date(row["dropoff_date"]),
                "domain": "expedia.com"
            })
    return configs

# Main scraping function
def run_scraper(config):
    options = uc.ChromeOptions()
    options.add_argument('start-maximized')
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    driver.get("https://www.expedia.com/")
    wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Cars"]'))).click()

    # Pickup location
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Pick-up"]'))).click()
    pickup_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-stid="pick_up_location-menu-input"]')))
    for c in config["pickup_location"]:
        pickup_input.send_keys(c)
        sleep(0.2)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-stid="pick_up_location-result-item-button"]')))
    pickup_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-stid="pick_up_location-result-item-button"]')

    for btn in pickup_buttons:
        label = btn.get_attribute("aria-label")
        if label and config["pickup_label_contains"].lower() in label.lower():
            btn.click()
            break

    # Drop-off location
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Drop-off, Same as pick-up"]'))).click()
    drop_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-stid="drop_off_location-menu-input"]')))
    for c in config["dropoff_location"]:
        drop_input.send_keys(c)
        sleep(0.2)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-stid="drop_off_location-result-item-button"]')))
    drop_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-stid="drop_off_location-result-item-button"]')

    for btn in drop_buttons:
        label = btn.get_attribute("aria-label")
        if label and config["dropoff_label_contains"].lower() in label.lower():
            btn.click()
            break

    # Dates
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="uitk-date-selector-input1-default"]'))).click()
    sleep(1)

    pickup_label = f'div[role="button"] div[aria-label="{config["pickup_date"]}"]'
    pickup_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, pickup_label)))
    pickup_elem.find_element(By.XPATH, './..').click()

    dropoff_label = f'div[role="button"] div[aria-label="{config["dropoff_date"]}"]'
    dropoff_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, dropoff_label)))
    dropoff_elem.find_element(By.XPATH, './..').click()

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-stid="apply-date-selector"]'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'search_button'))).click()

    # Wait for car results
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.offer-card-desktop')))

    # Show more if present
    def show_all():
        while True:
            sleep(3)
            try:
                driver.find_element(By.CSS_SELECTOR, 'button#paginationShowMoreBtn').click()
            except:
                break
    show_all()

    # Scrape
    scrape_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    car_cards = driver.find_elements(By.CSS_SELECTOR, 'li.offer-card-desktop')
    car_data = []
    for idx, card in enumerate(car_cards, start=1):
        try:
            name = card.find_element(By.CSS_SELECTOR, 'h3.uitk-heading').text
            price = card.find_element(By.CSS_SELECTOR, 'span.total-price').text
            provider = card.find_element(By.CSS_SELECTOR, 'img[alt]').get_attribute('alt')
            desc = card.find_element(By.CSS_SELECTOR, 'div.uitk-text-default-theme').text
            car_data.append((name, price, provider, desc, scrape_time, idx, config["domain"]))
        except:
            continue

    # Save to JSON
    json_data = []
    for row in car_data:
        json_data.append({
            "car_type": row[0],
            "price": row[1],
            "provider": row[2],
            "description": row[3],
            "scrape_time": row[4],
            "car_rank": row[5],
            "domain": row[6]
        })

    with open("car_data.json", "w") as f:
        json.dump(json_data, f, indent=4)

    driver.quit()

# Run from CSV
if __name__ == "__main__":
    input_configs = load_json_config("config.json")
    for conf in input_configs:
        run_scraper(conf)


