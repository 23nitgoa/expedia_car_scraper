import subprocess
import json
import os
from hotspot_switcher import rotate_hotspot
from store_results import store_car_listings
from datetime import datetime, timedelta
import random
import csv

CONFIG_PATH = "config.json"
SCRAPER_FOLDER = "scraper"

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

locations = config["locations"]
rental_sources = [s for s in config["rental_sources"] if s["enabled"]]
scraper_conf = config["scraper_config"][0]

scrape_horizon_days = scraper_conf["scrape_horizon_days"]
max_rental_duration_days = scraper_conf["max_rental_duration_days"]
start_offset = scraper_conf.get("scrape_start_offset_days", 0)

def generate_date_pairs():
    today = datetime.today().date()
    for pickup_offset in range(start_offset, start_offset + scrape_horizon_days + 1):
        pickup_date = today + timedelta(days=pickup_offset)
        for duration in range(max_rental_duration_days + 1):
            dropoff_date = pickup_date + timedelta(days=duration)
            yield (pickup_date.strftime('%Y-%m-%d'), dropoff_date.strftime('%Y-%m-%d'))

date_pairs = list(generate_date_pairs())

tasks = []

for source in rental_sources:
    domain = source["domain"]
    scraper_filename = f"{domain}_car_scraper.py"
    scraper_path = os.path.join(SCRAPER_FOLDER, scraper_filename)

    if not os.path.exists(scraper_path):
        print(f"[SKIP] Scraper not found: {scraper_path}")
        continue

    for loc in locations:
        pickup = loc["pickup_branch"]
        dropoff = loc["dropoff_branch"]

        for pickup_date, dropoff_date in date_pairs:
            tasks.append({
                "domain": domain,
                "scraper": scraper_filename,
                "pickup": pickup,
                "dropoff": dropoff,
                "start_date": pickup_date,
                "end_date": dropoff_date
            })
random.shuffle(tasks)

with open("intermediate_tasks.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["domain", "pickup", "dropoff", "start_date", "end_date"])
    writer.writeheader()
    for task in tasks:
        writer.writerow({
            "domain": task["domain"],
            "pickup": task["pickup"],
            "dropoff": task["dropoff"],
            "start_date": task["start_date"],
            "end_date": task["end_date"]
        })

for task in tasks:
    print(f"\n[INFO] Scraping {task['domain']} | {task['pickup']} ➝ {task['dropoff']} | {task['start_date']} → {task['end_date']}")
    rotate_hotspot()

    result = subprocess.run([
        "python", os.path.join(SCRAPER_FOLDER, task["scraper"]),
        "--pickup", task["pickup"],
        "--dropoff", task["dropoff"],
        "--start_date", task["start_date"],
        "--end_date", task["end_date"]
    ])

    if result.returncode != 0:
        print(f"[ERROR] {task['scraper']} failed with code {result.returncode}")
    else:
        print(f"[DONE] Completed: {task['pickup']} ➝ {task['dropoff']} | {task['start_date']} → {task['end_date']}")
        try:
            store_car_listings()
        except Exception as e:
            print(f"[ERROR] Failed to store results: {e}")
