from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# @app.route("/")
# def dashboard():

#     conn = sqlite3.connect("hospital.db")
#     cursor = conn.cursor()

#     cursor.execute("SELECT * FROM medicines")
    
#     medicines = cursor.fetchall()

#     total_medicines = len(medicines)
#     total_stock = 0
#     expiring_soon = 0
#     expired = 0

#     today = datetime.today()

#     for medicine in medicines:

#         quantity = medicine[3]
#         expiry_date = medicine[4]

#         total_stock += quantity

#         expiry_date = datetime.strptime(
#             expiry_date,
#             "%Y-%m-%d"
#         )

#         days_left = (expiry_date - today).days

#         if days_left < 0:
#             expired += 1

#         elif days_left <= 30:
#             expiring_soon += 1

#     conn.close()

#     return render_template(
#         "dashboard.html",
#         total_medicines=total_medicines,
#         total_stock=total_stock,
#         expiring_soon=expiring_soon,
#         expired=expired
#     )

@app.route("/")
def dashboard():

    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM medicines")
    medicines = cursor.fetchall()

    total_medicines = len(medicines)
    total_stock = 0
    expiring_soon = 0
    expired = 0

    manufacturer_data = {}

    today = datetime.today()

    for medicine in medicines:

        quantity = medicine[3]
        expiry_date = medicine[4]
        manufacturer = medicine[2]

        total_stock += quantity

        # Manufacturer chart data
        if manufacturer in manufacturer_data:
            manufacturer_data[manufacturer] += quantity
        else:
            manufacturer_data[manufacturer] = quantity

        # Expiry calculation
        expiry_date = datetime.strptime(
            expiry_date,
            "%Y-%m-%d"
        )

        days_left = (expiry_date - today).days

        if days_left < 0:
            expired += 1

        elif days_left <= 30:
            expiring_soon += 1

    conn.close()

    labels = list(manufacturer_data.keys())
    stock_values = list(manufacturer_data.values())

    return render_template(
        "dashboard.html",
        total_medicines=total_medicines,
        total_stock=total_stock,
        expiring_soon=expiring_soon,
        expired=expired,
        labels=labels,
        stock_values=stock_values
    )
    
@app.route("/add", methods=["GET", "POST"])
def add_medicine():

    if request.method == "POST":

        name = request.form["name"]
        manufacturer = request.form["manufacturer"]
        quantity = request.form["quantity"]
        expiry_date = request.form["expiry_date"]

        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO medicines
        (name, manufacturer, quantity, expiry_date)
        VALUES (?, ?, ?, ?)
        """,
        (name, manufacturer, quantity, expiry_date))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_medicine.html")

if __name__ == "__main__":
    app.run(debug=True)