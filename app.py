from flask import Flask, render_template, request, redirect, session
import psycopg2
import random
import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ----------------------------
# DATABASE CONNECTION
# ----------------------------

def connect():
    database_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    return conn


# ----------------------------
# IMEI GENERATOR
# ----------------------------

def generate_imei():
    return str(random.randint(100000000000000, 999999999999999))


# ----------------------------
# LANDING PAGE
# ----------------------------

@app.route("/")
def landing():
    return render_template("landing.html")


# ----------------------------
# STORE PAGE
# ----------------------------

@app.route("/store")
def store():

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products")

    products = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("home.html", products=products)


# ----------------------------
# PRODUCT DETAILS
# ----------------------------

@app.route("/product/<int:id>")
def product(id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id=%s", (id,))

    product = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("product.html", product=product)


# ----------------------------
# ADD TO CART
# ----------------------------

@app.route("/add_to_cart/<int:id>")
def add_to_cart(id):

    if "cart" not in session:
        session["cart"] = []

    cart = session["cart"]
    cart.append(id)

    session["cart"] = cart

    return redirect("/cart")


# ----------------------------
# CART PAGE
# ----------------------------

@app.route("/cart")
def cart():

    if "cart" not in session:
        session["cart"] = []

    ids = session["cart"]

    conn = connect()
    cur = conn.cursor()

    products = []

    for i in ids:

        cur.execute("SELECT * FROM products WHERE id=%s", (i,))
        product = cur.fetchone()

        if product:
            products.append(product)

    cur.close()
    conn.close()

    return render_template("cart.html", products=products)


# ----------------------------
# CHECKOUT
# ----------------------------

@app.route("/checkout/<int:id>")
def checkout(id):

    imei = generate_imei()

    purchase_date = datetime.date.today()
    warranty = purchase_date + datetime.timedelta(days=365)

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders(product_id, imei, purchase_date, warranty_expiry) VALUES(%s,%s,%s,%s)",
        (id, imei, purchase_date, warranty)
    )

    conn.commit()

    cur.close()
    conn.close()

    order = {
        "imei": imei,
        "purchase": purchase_date,
        "warranty": warranty
    }

    return render_template("invoice.html", order=order)


# ----------------------------
# USER REGISTER
# ----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (name, email, password)
        )

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ----------------------------
# USER LOGIN
# ----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            return redirect("/store")

    return render_template("login.html")


# ----------------------------
# SERVICE CENTER
# ----------------------------

@app.route("/service", methods=["GET", "POST"])
def service():

    message = ""

    if request.method == "POST":

        imei = request.form["imei"]
        problem = request.form["problem"]

        conn = connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT warranty_expiry FROM orders WHERE imei=%s",
            (imei,)
        )

        order = cur.fetchone()

        if order:

            expiry = datetime.datetime.strptime(str(order[0]), "%Y-%m-%d").date()

            if expiry >= datetime.date.today():

                cur.execute(
                    "INSERT INTO service_requests(imei,problem,request_date) VALUES(%s,%s,%s)",
                    (imei, problem, datetime.date.today())
                )

                conn.commit()

                message = "Warranty valid. Service request booked."

            else:
                message = "Warranty expired."

        else:
            message = "Invalid IMEI."

        cur.close()
        conn.close()

    return render_template("service.html", message=message)


# ----------------------------
# ADMIN LOGIN
# ----------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            return redirect("/admin_dashboard")

    return render_template("admin_login.html")


# ----------------------------
# ADMIN DASHBOARD
# ----------------------------

@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():

    conn = connect()
    cur = conn.cursor()

    if request.method == "POST":

        brand = request.form["brand"]
        model = request.form["model"]
        price = request.form["price"]

        image = request.files["image"]

        filename = secure_filename(image.filename)

        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        cur.execute(
            "INSERT INTO products(brand,model,price,image) VALUES(%s,%s,%s,%s)",
            (brand, model, price, filename)
        )

        conn.commit()

    cur.execute("SELECT * FROM products")
    products = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin_dashboard.html", products=products)


# ----------------------------
# DELETE PRODUCT
# ----------------------------

@app.route("/delete_product/<int:id>")
def delete_product(id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM products WHERE id=%s",
        (id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/admin_dashboard")


# ----------------------------
# RUN APP
# ----------------------------

if __name__ == "__main__":
    app.run(debug=True)