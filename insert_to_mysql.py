import os
import json
import mysql.connector
from mysql.connector import Error

def insert_data_to_mysql(base_folder):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='harsh123',
            database='expedia_data'
        )

        if connection.is_connected():
            cursor = connection.cursor()

            insert_query = """
            INSERT INTO car_listings (
                car_type, price, vendor, description,
                capacity, transmission, mileage, 
                policies, vendor_rating, image_file,
                scrape_time, car_rank, domain, image_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            for run_folder in sorted(os.listdir(base_folder)):
                run_path = os.path.join(base_folder, run_folder)
                json_path = os.path.join(run_path, "car_data.json")
                image_dir = os.path.join(run_path, "car_images")

                if os.path.isfile(json_path):
                    with open(json_path, 'r') as file:
                        car_data = json.load(file)
                    for car in car_data:
                        image_file = car.get("image_file", "")
                        rel_image_path = os.path.join(image_dir, image_file)
                        abs_image_path = os.path.abspath(rel_image_path)

                        cursor.execute(insert_query, (
                            car.get("car_type"),
                            car.get("price"),
                            car.get("vendor"),
                            car.get("description"),
                            car.get("capacity"),
                            car.get("transmission"),
                            car.get("mileage"),
                            ", ".join(car.get("policies", [])),
                            car.get("vendor_rating"),
                            image_file,
                            car.get("scrape_time"),
                            car.get("rank"),
                            car.get("domain"),
                            abs_image_path
                        ))

            connection.commit()
            print("All car data from folder inserted successfully.")

    except Error as e:
        print("Error while connecting to MySQL:", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    insert_data_to_mysql("car_information_storage")
