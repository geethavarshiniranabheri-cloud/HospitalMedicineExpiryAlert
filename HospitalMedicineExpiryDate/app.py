from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

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

    urgent_medicines = []
    manufacturer_data = {}

    today = datetime.today()

    for medicine in medicines:

        quantity = medicine[3]
        expiry_date = medicine[4]
        manufacturer = medicine[2]

        total_stock += quantity

        # Manufacturer Chart
        if manufacturer in manufacturer_data:
            manufacturer_data[manufacturer] += quantity
        else:
            manufacturer_data[manufacturer] = quantity

        # Expiry Calculation
        expiry_date = datetime.strptime(
            expiry_date,
            "%Y-%m-%d"
        )

        days_left = (expiry_date - today).days

        if days_left < 0:
            expired += 1
            urgent_medicines.append((medicine, days_left))

        elif days_left <= 30:
            expiring_soon += 1
            urgent_medicines.append((medicine, days_left))

    conn.close()

    labels = list(manufacturer_data.keys())
    stock_values = list(manufacturer_data.values())

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        total_medicines=total_medicines,
        total_stock=total_stock,
        expiring_soon=expiring_soon,
        expired=expired,
        urgent_medicines=urgent_medicines,
        labels=labels,
        stock_values=stock_values
    )
    
# @app.route("/add", methods=["GET", "POST"])
# def add_medicine():

#     if request.method == "POST":

#         name = request.form["name"]
#         manufacturer = request.form["manufacturer"]
#         quantity = request.form["quantity"]
#         expiry_date = request.form["expiry_date"]

#         conn = sqlite3.connect("hospital.db")
#         cursor = conn.cursor()

#         cursor.execute("""
#         INSERT INTO medicines
#         (name, manufacturer, quantity, expiry_date)
#         VALUES (?, ?, ?, ?)
#         """,
#         (name, manufacturer, quantity, expiry_date))

#         conn.commit()
#         conn.close()

#         return redirect("/")

#     return render_template(
#     "add_medicine.html",
#     active_page="add"
#  )

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

    return render_template(
        "add_medicine.html",
        active_page="add"
    )

@app.route("/medicines")
def medicines():

    sort = request.args.get("sort", "expiry")

    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    if sort == "name":
        cursor.execute(
            "SELECT * FROM medicines ORDER BY name ASC"
        )

    elif sort == "quantity":
        cursor.execute(
            "SELECT * FROM medicines ORDER BY quantity DESC"
        )

    else:
        cursor.execute(
            "SELECT * FROM medicines ORDER BY expiry_date ASC"
        )

    medicines = cursor.fetchall()

    conn.close()

    medicine_list = []

    today = datetime.today()

    for medicine in medicines:

        expiry = datetime.strptime(
            medicine[4],
            "%Y-%m-%d"
        )

        days_left = (expiry - today).days

        if days_left < 0:
            status = "Expired"

        elif days_left <= 30:
            status = "Expiring Soon"

        else:
            status = "Safe"

        medicine_list.append({
            "id": medicine[0],
            "name": medicine[1],
            "manufacturer": medicine[2],
            "quantity": medicine[3],
            "expiry": medicine[4],
            "status": status
        })

    return render_template(
        "medicines.html",
        medicines=medicine_list,
        current_sort=sort,
        active_page="medicines"
    )

if __name__ == "__main__":
    app.run(debug=True)