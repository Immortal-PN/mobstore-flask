from flask import Flask, render_template, request, redirect, session
import sqlite3
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
    return sqlite3.connect("database.db")


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

    db = connect()

    products = db.execute(
        "SELECT * FROM products"
    ).fetchall()

    return render_template("home.html", products=products)


# ----------------------------
# PRODUCT DETAILS
# ----------------------------

@app.route("/product/<int:id>")
def product(id):

    db = connect()

    product = db.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    ).fetchone()

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

    db = connect()

    products = []

    for i in ids:

        product = db.execute(
            "SELECT * FROM products WHERE id=?",
            (i,)
        ).fetchone()

        if product:
            products.append(product)

    return render_template("cart.html", products=products)


# ----------------------------
# CHECKOUT
# ----------------------------

@app.route("/checkout/<int:id>")
def checkout(id):

    imei = generate_imei()

    purchase_date = datetime.date.today()

    warranty = purchase_date + datetime.timedelta(days=365)

    db = connect()

    db.execute(
        "INSERT INTO orders(product_id, imei, purchase_date, warranty_expiry) VALUES(?,?,?,?)",
        (id, imei, purchase_date, warranty)
    )

    db.commit()

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

        db = connect()

        db.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, password)
        )

        db.commit()

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

        db = connect()

        user = db.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

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

        db = connect()

        order = db.execute(
            "SELECT warranty_expiry FROM orders WHERE imei=?",
            (imei,)
        ).fetchone()

        if order:

            expiry = datetime.datetime.strptime(order[0], "%Y-%m-%d").date()

            if expiry >= datetime.date.today():

                db.execute(
                    "INSERT INTO service_requests(imei,problem,request_date) VALUES(?,?,?)",
                    (imei, problem, datetime.date.today())
                )

                db.commit()

                message = "Warranty valid. Service request booked."

            else:
                message = "Warranty expired."

        else:
            message = "Invalid IMEI."

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

    db = connect()

    if request.method == "POST":

        brand = request.form["brand"]
        model = request.form["model"]
        price = request.form["price"]

        image = request.files["image"]

        filename = secure_filename(image.filename)

        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.execute(
            "INSERT INTO products(brand,model,price,image) VALUES(?,?,?,?)",
            (brand, model, price, filename)
        )

        db.commit()

    products = db.execute("SELECT * FROM products").fetchall()

    return render_template("admin_dashboard.html", products=products)

@app.route("/delete_product/<int:id>")
def delete_product(id):

    db = connect()

    db.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )

    db.commit()

    return redirect("/admin_dashboard")


# ----------------------------
# RUN APP
# ----------------------------

if __name__ == "__main__":
    app.run(debug=True)