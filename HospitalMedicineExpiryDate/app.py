from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)

app.secret_key = "meditrack_secret_key"

@app.context_processor
def inject_notifications():

    return dict(
        notification_count=0,
        urgent_medicines=[]
    )

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username=? AND password=?
            """,
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session["user"] = username

            return redirect("/")

        return render_template(
            "login.html",
            error="Invalid Username or Password"
        )

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO users
            (fullname, username, email, password)
            VALUES (?, ?, ?, ?)
            """,
            (fullname, username, email, password))

            conn.commit()

            session["user"] = username

            return redirect("/")

        except:

            return render_template(
                "register.html",
                error="Username or Email already exists"
            )

        finally:
            conn.close()

    return render_template("register.html")

@app.route("/")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    # cursor.execute("SELECT * FROM medicines")
    
    username = session["user"]

    cursor.execute(
        "SELECT id FROM users WHERE username=?",
        (username,)
    )

    user_id = cursor.fetchone()[0]

    cursor.execute(
        "SELECT * FROM medicines WHERE user_id=?",
        (user_id,)
    )
    
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

    # labels = list(manufacturer_data.keys())
    # stock_values = list(manufacturer_data.values())
    
    sorted_data = sorted(
    manufacturer_data.items(),
    key=lambda x: x[1],
    reverse=True
    )

    labels = [item[0] for item in sorted_data]
    stock_values = [item[1] for item in sorted_data]
    notification_count = len(urgent_medicines)

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        total_medicines=total_medicines,
        total_stock=total_stock,
        expiring_soon=expiring_soon,
        expired=expired,
        urgent_medicines=urgent_medicines,
        labels=labels,
        stock_values=stock_values,
        notification_count=notification_count
    )
    

@app.route("/add", methods=["GET", "POST"])
def add_medicine():
    
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        name = request.form["name"]
        manufacturer = request.form["manufacturer"]
        quantity = request.form["quantity"]
        expiry_date = request.form["expiry_date"]
        
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()
        
        username = session["user"]

        cursor.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        )

        user_id = cursor.fetchone()[0]

        # conn = sqlite3.connect("hospital.db")
        # cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO medicines
        (name, manufacturer, quantity, expiry_date, user_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, manufacturer, quantity, expiry_date, user_id))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template(
        "add_medicine.html",
        active_page="add"
    )

@app.route("/medicines")
def medicines():
    
    if "user" not in session:
        return redirect("/login")
    
    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()
    
    username = session["user"]
    
    cursor.execute(
        "SELECT id FROM users WHERE username=?",
        (username,)
    )
    
    user_id = cursor.fetchone()[0]

    sort = request.args.get("sort", "expiry")

    # sort = request.args.get("sort", "expiry")

    # conn = sqlite3.connect("hospital.db")
    # username = session["user"]

    # cursor.execute(
    #     "SELECT id FROM users WHERE username=?",
    #     (username,)
    # )

    # user_id = cursor.fetchone()[0]
    # cursor = conn.cursor()

    if sort == "name":
        cursor.execute(
            "SELECT * FROM medicines WHERE user_id=? ORDER BY name ASC",
            (user_id,)
        )

    elif sort == "quantity":
        cursor.execute(
            "SELECT * FROM medicines WHERE user_id=? ORDER BY quantity DESC",
            (user_id,)
        )

    else:
        cursor.execute(
            "SELECT * FROM medicines WHERE user_id=? ORDER BY expiry_date ASC",
            (user_id,)
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
    
@app.route("/delete/<int:id>")
def delete_medicine(id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM medicines WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/medicines")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_medicine(id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        manufacturer = request.form["manufacturer"]
        quantity = request.form["quantity"]
        expiry_date = request.form["expiry_date"]

        cursor.execute("""
        UPDATE medicines
        SET name=?,
            manufacturer=?,
            quantity=?,
            expiry_date=?
        WHERE id=?
        """,
        (
            name,
            manufacturer,
            quantity,
            expiry_date,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/medicines")

    cursor.execute(
        "SELECT * FROM medicines WHERE id=?",
        (id,)
    )

    medicine = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_medicine.html",
        medicine=medicine
    )

@app.route("/reports")
def reports():

    # cursor.execute("SELECT * FROM medicines")
    
    username = session["user"]

    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username=?",
        (username,)
    )

    user_id = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT * FROM medicines WHERE user_id=?",
        (user_id,)
   )  
    
    medicines = cursor.fetchall()

    conn.close()

    expiring_medicines = []
    expired_medicines = []

    today = datetime.today()

    for medicine in medicines:

        expiry = datetime.strptime(
            medicine[4],
            "%Y-%m-%d"
        )

        days_left = (expiry - today).days

        if days_left < 0:

            expired_medicines.append({
                "name": medicine[1],
                "manufacturer": medicine[2],
                "expiry": medicine[4]
            })

        elif days_left <= 30:

            expiring_medicines.append({
                "name": medicine[1],
                "manufacturer": medicine[2],
                "expiry": medicine[4],
                "days_left": days_left
            })

    return render_template(
        "reports.html",
        expiring_medicines=expiring_medicines,
        expired_medicines=expired_medicines,
        active_page="reports"
    )
    
@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)