import os
import json
import requests
from datetime import datetime

def store_car_listings():
    with open("car_data_temp.json", "r", encoding="utf-8") as f:
        temp_data = json.load(f)

    car_data = temp_data["car_data"]
    config = temp_data["config"]
    scrape_time = temp_data["scrape_time"]

    base_dir = "car_information_storage"
    os.makedirs(base_dir, exist_ok=True)

    existing_runs = [name for name in os.listdir(base_dir) if name.startswith("run_")]
    run_counter = len(existing_runs) + 1

    run_dir = os.path.join(base_dir, f"run_{run_counter}")
    image_dir = os.path.join(run_dir, "car_images")
    os.makedirs(image_dir, exist_ok=True)

    for idx, car in enumerate(car_data, 1):
        try:
            image_url = car.get("image_file")
            image_name = f"car_{idx}.jpg"
            image_path = os.path.join(image_dir, image_name)

            if image_url:
                with open(image_path, 'wb') as img_file:
                    img_file.write(requests.get(image_url).content)

            car["image_file"] = image_name
        except Exception as e:
            print(f"[ERROR] Could not save image for car #{idx}: {e}")

    with open(os.path.join(run_dir, "car_data.json"), "w", encoding="utf-8") as f:
        json.dump(car_data, f, indent=4, ensure_ascii=False)

    print(f"[STORAGE] Saved run_{run_counter} with {len(car_data)} cars.")
