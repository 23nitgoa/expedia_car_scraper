# Expedia Car Scraper 

A Python-based project that scrapes car rental listings from [Expedia](https://www.expedia.com) using Playwright, and stores results in JSON and MySQL.

## Features
- Dynamic location and date input via `config.json`
- Scrapes car type, price, provider, and more
- Stores results in both `car_data.json` and MySQL
- Configurable and scalable architecture

## Requirements

Install dependencies with:

```bash
## How to Run
pip install -r requirements.txt

# Install Playwright drivers (once)
playwright install

# Run scraper
python run_scraper.py

# Push data to MySQL
python insert_into_mysql.py

##Edit config.json

[
  {
    "pickup_location": "San Francisco",
    "pickup_label_contains": "San Francisco",
    "dropoff_location": "Los Angeles",
    "dropoff_label_contains": "Los Angeles",
    "pickup_date": "Monday, June 2, 2025",
    "dropoff_date": "Tuesday, June 3, 2025",
    "domain": "expedia.com"
  }
]


