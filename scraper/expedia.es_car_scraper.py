import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
from time import sleep
import json
import os
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--pickup", required=True)
parser.add_argument("--dropoff", required=True)
parser.add_argument("--start_date", required=True)
parser.add_argument("--end_date", required=True)
args = parser.parse_args()

def format_expedia_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%A, %B %d, %Y").replace(" 0", " ")

config = {
    "pickup_location": args.pickup,
    "pickup_label_contains": args.pickup,
    "dropoff_location": args.dropoff,
    "dropoff_label_contains": args.dropoff,
    "pickup_date": format_expedia_date(args.start_date),
    "dropoff_date": format_expedia_date(args.end_date),
    "domain": "expedia.es"
}

def go_to_target_month(driver, wait, target_month_year):
    max_tries = 12
    for _ in range(max_tries):
        visible_months = driver.find_elements(By.XPATH, '//span[contains(@class, "uitk-month-label")]')
        visible_texts = [m.text.strip() for m in visible_months if m.text.strip()]

        if target_month_year in visible_texts:
            return  
        prev_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-stid="uitk-calendar-navigation-controls-previous-button"]')
        if prev_buttons:
            prev_buttons[0].click()
            sleep(0.5)
        else:
            print(f"[INFO] Reached earliest calendar month, but {target_month_year} not visible.")
            raise Exception(f"Target month {target_month_year} not found in calendar.") 
        
def run_scraper(config):

    options = uc.ChromeOptions()
    options.add_argument('start-maximized')
    options.add_argument("--lang=en")
    options.add_experimental_option(
        "prefs", {"translate_whitelists": {"es": "en"}, "translate": {"enabled": True}}
    )

    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    driver.get("https://www.expedia.es/Cars")
    
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_btn.click()
        print("Cookie banner accepted.")

        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "onetrust-policy-text"))
        )
        print("Cookie banner fully removed.")
    except:
        print("No cookie banner or already dismissed.")
    
    sleep(0.2)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Collection"]'))).click()
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

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label^="Delivery"]'))).click()
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
    pickup_month_year = " ".join(config["pickup_date"].split(" ")[2:4])
    go_to_target_month(driver, wait, pickup_month_year)

    pickup_day = str(int(datetime.strptime(config["pickup_date"], "%A, %B %d, %Y").day))
    pickup_xpath = f'//div[contains(@class, "uitk-date-number") and normalize-space()="{pickup_day}"]/ancestor::div[@role="button"]'

    pickup_elem = wait.until(EC.element_to_be_clickable((By.XPATH, pickup_xpath)))
    pickup_elem.click()
    sleep(0.5)

    if config["pickup_date"] == config["dropoff_date"]:
        driver.execute_script("arguments[0].click();", pickup_elem)
    else:
        sleep(0.5)
        dropoff_label = config["dropoff_date"]
        try:
            dropoff_elem = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                f'//div[@role="button"]//div[contains(@aria-label, "{dropoff_label}")]//ancestor::div[@role="button"]')))
            dropoff_elem.click()
        except:
            print(" ")

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-stid="apply-date-selector"]'))).click()

    now = datetime.now()
    pickup_select = Select(wait.until(EC.presence_of_element_located((By.ID, "pick_up_time"))))

    selected_value = None
    for option in pickup_select.options:
        try:
            opt_time = datetime.strptime(option.get_attribute("value"), "%I%M%p")
            opt_today = now.replace(hour=opt_time.hour, minute=opt_time.minute, second=0, microsecond=0)
            if opt_today > now:
                selected_value = option.get_attribute("value")
                break
        except Exception as e:
            continue

    if selected_value:
        pickup_select.select_by_value(selected_value)
        pickup_time_obj = datetime.strptime(selected_value, "%I%M%p")
    else:
        pickup_select.select_by_index(1)

    drop_select = Select(wait.until(EC.presence_of_element_located((By.ID, "drop_off_time"))))

    for option in drop_select.options:
        try:
            drop_val = option.get_attribute("value")
            drop_time = datetime.strptime(drop_val, "%I%M%p")
            if drop_time.time() >= (pickup_time_obj + timedelta(hours=3)).time():
                drop_select.select_by_value(drop_val)
                break
        except:
            continue

    wait.until(EC.element_to_be_clickable((By.ID, 'search_button'))).click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.offer-card-desktop')))
    for i in range(5):
        try:
            show_more_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#paginationShowMoreBtn')))
            print(f"[INFO] Clicking 'Show more' button (attempt {i+1})...")
            driver.execute_script("arguments[0].click();", show_more_btn)
            sleep(2)
        except:
            print(f"[INFO] No more 'Show more' button or finished after {i} attempts.")
            break

    scrape_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    car_cards = driver.find_elements(By.CSS_SELECTOR, 'li.offer-card-desktop')

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

            total_price = car.find_element(By.CSS_SELECTOR, "div.uitk-type-bold.total-price-subtext").text
            image_url = car.find_element(By.CSS_SELECTOR, 'img.uitk-image-media').get_attribute('src')


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
                "image_file": image_url,
                "scrape_time": scrape_time,
                "domain": config["domain"]
            })

        except Exception as e:
            print(f"Error processing car #{idx}: {e}")

    with open("car_data_temp.json", "w", encoding="utf-8") as f:
        json.dump({
            "car_data": car_data,
            "config": config,
            "scrape_time": scrape_time
        }, f, indent=4, ensure_ascii=False)

    driver.quit()

if __name__ == "__main__":
    run_scraper(config)