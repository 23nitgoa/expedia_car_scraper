import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
from time import sleep
import json
import os
import shutil
import requests

def format_expedia_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_day = dt.strftime("%d").lstrip("0")
    return dt.strftime(f"%A, %B {formatted_day}, %Y")

def generate_date_ranges(scrape_horizon_days, max_rental_duration_days, start_offset_days=0):
    today = datetime.today().date()
    date_pairs = []
    for pickup_offset in range(start_offset_days, start_offset_days + scrape_horizon_days + 1):
        pickup_date = today + timedelta(days=pickup_offset)
        for rental_duration in range(max_rental_duration_days + 1):
            dropoff_date = pickup_date + timedelta(days=rental_duration)
            date_pairs.append((pickup_date.strftime('%Y-%m-%d'), dropoff_date.strftime('%Y-%m-%d')))
    return date_pairs

def load_json_config(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

run_counter = 1
previous_config_signature = None

def run_scraper(config):
    global run_counter, previous_config_signature

    current_signature = f"{config['pickup_location']}__{config['dropoff_location']}"

    if previous_config_signature and current_signature != previous_config_signature:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{previous_config_signature}_{timestamp}"
        if os.path.exists("car_information_storage"):
            shutil.move("car_information_storage", backup_name)
            print(f"Backed up previous data to: {backup_name}")
        run_counter = 1
    previous_config_signature = current_signature

    options = uc.ChromeOptions()
    options.add_argument('start-maximized')
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    driver.get("https://www.expedia.com/")
    wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Cars"]'))).click()

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Pick-up"]'))).click()
    pickup_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-stid="pick_up_location-menu-input"]')))
    pickup_input.clear()
    for c in config["pickup_location"]:
        pickup_input.send_keys(c)
        sleep(0.2)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-stid="pick_up_location-result-item-button"]')))
    pickup_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-stid="pick_up_location-result-item-button"]')
    for btn in pickup_buttons:
        label = btn.get_attribute("aria-label")
        if label and config["pickup_location"].lower() in label.lower():
            btn.click()
            break

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label^="Drop-off"]'))).click()
    drop_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-stid="drop_off_location-menu-input"]')))
    drop_input.clear()
    for c in config["dropoff_location"]:
        drop_input.send_keys(c)
        sleep(0.2)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-stid="drop_off_location-result-item-button"]')))
    drop_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-stid="drop_off_location-result-item-button"]')
    for btn in drop_buttons:
        label = btn.get_attribute("aria-label")
        if label and config["dropoff_location"].lower() in label.lower():
            btn.click()
            break

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="uitk-date-selector-input1-default"]'))).click()
    sleep(1)

    pickup_label = f'div[role="button"] div[aria-label="{config["pickup_date"]}"]'
    pickup_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, pickup_label)))
    pickup_parent = pickup_elem.find_element(By.XPATH, './..')
    pickup_parent.click()
    sleep(0.5)

    if config["pickup_date"] == config["dropoff_date"]:
        driver.execute_script("arguments[0].click();", pickup_parent)
    else:
        sleep(0.5)
        dropoff_label = f'div[role="button"] div[aria-label="{config["dropoff_date"]}"]'
        try:
            dropoff_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, dropoff_label)))
            dropoff_elem.find_element(By.XPATH, './..').click()
        except:
            print("Drop-off already selected or not clickable")

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-stid="apply-date-selector"]'))).click()
    if config["pickup_date"] == config["dropoff_date"]:
        # Ensure the dropdown is present
        pickup_select_element = wait.until(EC.presence_of_element_located((By.ID, "pick_up_time")))

        # Use Select to choose '10:30am'
        select = Select(pickup_select_element)
        select.select_by_visible_text("10:30am")
        pickup_time_str = "10:30am"

        min_drop_time = datetime.strptime(pickup_time_str, "%I:%M%p") + timedelta(hours=2)
        dropoff_time_str = min_drop_time.strftime("%I:%M%p").lower()
        if dropoff_time_str.startswith('0'):
            dropoff_time_str = dropoff_time_str[1:]


        wait.until(EC.element_to_be_clickable((By.ID, "drop_off_time"))).click()
            # Initialize the Select object
        drop_select = Select(driver.find_element(By.ID, "drop_off_time"))

        # Loop through all drop-off time options
        for option in drop_select.options:
            time_text = option.text.strip().lower()

            try:
                if not time_text or ':' not in time_text:
                    continue

                if time_text.startswith('0'):
                    time_text = time_text[1:]

                option_time = datetime.strptime(time_text, "%I:%M%p")

                if option_time >= min_drop_time:
                    drop_select.select_by_visible_text(option.text)
                    break
            except Exception as e:
                print(f"Skipping option '{option.text}': {e}")
                
    wait.until(EC.element_to_be_clickable((By.ID, 'search_button'))).click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.offer-card-desktop')))

    scrape_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    car_cards = driver.find_elements(By.CSS_SELECTOR, 'li.offer-card-desktop')

    base_dir = "car_information_storage"
    run_dir = os.path.join(base_dir, f"run_{run_counter}")
    image_dir = os.path.join(run_dir, "car_images")
    os.makedirs(image_dir, exist_ok=True)

    car_data = []
    for idx, car in enumerate(car_cards, 1):
        try:
            car_type = car.find_element(By.CSS_SELECTOR, 'h3.uitk-heading').text
            description = car.find_element(By.CSS_SELECTOR, 'div.uitk-text.uitk-type-300').text
            attributes = car.find_elements(By.CSS_SELECTOR, 'span.text-attribute')
            capacity = attributes[0].text if len(attributes) > 0 else ""
            transmission = attributes[1].text if len(attributes) > 1 else ""
            mileage = ""
            try:
                mileage = car.find_element(By.XPATH, ".//*[contains(text(), 'mileage')]").text
            except:
                pass
            policies = [el.text for el in car.find_elements(By.CSS_SELECTOR, '.confidence-messages div.uitk-text')]
            vendor_logo = car.find_element(By.CSS_SELECTOR, 'img.vendor-logo').get_attribute('alt')
            try:
                vendor_rating = car.find_element(By.CSS_SELECTOR, '.uitk-badge-base-text').text
            except:
                vendor_rating = ""

            total_price = car.find_element(By.CSS_SELECTOR, 'span.total-price').text
            image_url = car.find_element(By.CSS_SELECTOR, 'img.uitk-image-media').get_attribute('src')

            image_name = f"car_{idx}.jpg"
            image_path = os.path.join(image_dir, image_name)
            with open(image_path, 'wb') as img_file:
                img_file.write(requests.get(image_url).content)

            car_data.append({
                "rank": idx,
                "car_type": car_type,
                "description": description,
                "capacity": capacity,
                "transmission": transmission,
                "mileage": mileage,
                "policies": policies,
                "vendor": vendor_logo,
                "vendor_rating": vendor_rating,
                "price": total_price,
                "image_file": image_name,
                "scrape_time": scrape_time,
                "domain": config["domain"]
            })

        except Exception as e:
            print(f"Error processing car #{idx}: {e}")

    json_path = os.path.join(run_dir, "car_data.json")
    with open(json_path, "w") as f:
        json.dump(car_data, f, indent=4)
    sleep(0.5)

    run_counter += 1
    driver.quit()

if __name__ == "__main__":
    raw_config = load_json_config("config.json")
    locations = raw_config["locations"]
    rental_sources = [s for s in raw_config["rental_sources"] if s["enabled"] and s["name"] == "Expedia"]
    scraper_conf = raw_config["scraper_config"][0]  # if it's a list

    date_pairs = generate_date_ranges(
    scrape_horizon_days=scraper_conf["scrape_horizon_days"],
    max_rental_duration_days=scraper_conf["max_rental_duration_days"],
    start_offset_days=scraper_conf.get("scrape_start_offset_days", 0)
)


    for source in rental_sources:
        for loc in locations:
            for pickup_date, dropoff_date in date_pairs:
                config = {
                    "pickup_location": loc["pickup_branch"],
                    "pickup_label_contains": loc["pickup_branch"],
                    "dropoff_location": loc["dropoff_branch"],
                    "dropoff_label_contains": loc["dropoff_branch"],
                    "pickup_date": format_expedia_date(pickup_date),
                    "dropoff_date": format_expedia_date(dropoff_date),
                    "domain": source["domain"]
                }
                run_scraper(config)
