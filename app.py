from flask import Flask, render_template_string
import mysql.connector

app = Flask(__name__)

@app.route("/")
def show_cars():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="harsh123",
        database="expedia_data"
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT car_type, price, vendor, description, 
               image_path, scrape_time, car_rank 
        FROM car_listings ORDER BY scrape_time DESC, car_rank ASC
    """)
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    html = """
    <html><head><title>Expedia Car Listings</title></head>
    <body style="font-family:Arial;">
    <h2>Car Listings</h2>
    <div style='display:flex; flex-wrap:wrap;'>
    {% for car in cars %}
        <div style='border:1px solid #ccc; margin:10px; padding:10px; width:250px;'>
            <img src='{{ car[4] }}' style='width:100%; height:auto'><br>
            <b>{{ car[0] }}</b><br>
            <i>{{ car[1] }}</i><br>
            <small>{{ car[2] }}</small><br>
            <small>Rank: {{ car[6] }}</small><br>
            <p>{{ car[3][:100] }}...</p>
            <small>Scraped at: {{ car[5] }}</small>
        </div>
    {% endfor %}
    </div></body></html>
    """
    return render_template_string(html, cars=records)

if __name__ == "__main__":
    app.run(debug=True)
