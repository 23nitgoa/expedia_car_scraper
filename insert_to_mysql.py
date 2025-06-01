# insert_into_mysql.py
import json
import mysql.connector
from mysql.connector import Error

def insert_data_to_mysql(json_path):
    try:
        with open(json_path, 'r') as file:
            car_data = json.load(file)

        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='harsh123',
            database='expedia'
        )

        if connection.is_connected():
            cursor = connection.cursor()

            insert_query = """
            INSERT INTO car_listings (car_type, price, provider, description, scrape_time, car_rank, domain)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            data_to_insert = [
                (
                    car['car_type'],
                    car['price'],
                    car['provider'],
                    car['description'],
                    car['scrape_time'],
                    car['car_rank'],
                    car['domain']
                ) for car in car_data
            ]

            cursor.executemany(insert_query, data_to_insert)
            connection.commit()
            print(f"{cursor.rowcount} records inserted successfully.")

    except Error as e:
        print("Error while connecting to MySQL:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    insert_data_to_mysql("car_data.json")
