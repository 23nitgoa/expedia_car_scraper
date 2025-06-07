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

{
  "locations": [
    {
      "pickup_branch": "New York Airport",
      "dropoff_branch": "New York Airport"
    }
  ],
  "rental_sources": [
    {
      "name": "Expedia",
      "enabled": true,
      "domain": "expedia.com"
    }
  ],
  "scraper_config": [
  {
    "scrape_horizon_days": 2,
    "max_rental_duration_days": 1,
    "scrape_start_offset_days": 1
  } 
  ]
}


