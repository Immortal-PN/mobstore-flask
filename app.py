from flask import Flask, render_template, request, redirect, session
import psycopg2
import random
import datetime
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

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
# INITIALIZE DATABASE
# ----------------------------

def init_db():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id SERIAL PRIMARY KEY,
        brand VARCHAR(100),
        model VARCHAR(100),
        price NUMERIC,
        image TEXT,
        ram VARCHAR(20),
        storage VARCHAR(20),
        battery VARCHAR(20),
        category VARCHAR(50)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(
        id SERIAL PRIMARY KEY,
        username VARCHAR(100),
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id SERIAL PRIMARY KEY,
        user_email VARCHAR(100),
        product_id INTEGER,
        quantity INTEGER,
        total_price NUMERIC,
        imei VARCHAR(50),
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS service_requests(
        id SERIAL PRIMARY KEY,
        imei VARCHAR(50),
        issue TEXT,
        status VARCHAR(50) DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


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

    cur.execute("SELECT * FROM products WHERE id=%s",(id,))
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
        session["cart"] = {}

    cart = session["cart"]

    if str(id) in cart:
        cart[str(id)] += 1
    else:
        cart[str(id)] = 1

    session["cart"] = cart

    return redirect("/cart")


# ----------------------------
# CART PAGE
# ----------------------------

@app.route("/cart")
def cart():

    cart = session.get("cart",{})

    conn = connect()
    cur = conn.cursor()

    items = []
    total = 0

    for pid,qty in cart.items():

        cur.execute("SELECT * FROM products WHERE id=%s",(pid,))
        product = cur.fetchone()

        if product:

            subtotal = product[3] * qty
            total += subtotal

            items.append({
                "product":product,
                "qty":qty,
                "subtotal":subtotal
            })

    cur.close()
    conn.close()

    return render_template("cart.html", items=items, total=total)


# ----------------------------
# CHECKOUT
# ----------------------------

@app.route("/checkout/<int:id>")
def checkout(id):

    imei = generate_imei()

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT price FROM products WHERE id=%s",(id,))
    price = cur.fetchone()[0]

    cur.execute(
    "INSERT INTO orders(user_email,product_id,quantity,total_price,imei) VALUES(%s,%s,%s,%s,%s)",
    ("guest",id,1,price,imei)
    )

    conn.commit()

    cur.close()
    conn.close()

    order = {
        "imei": imei,
        "date": datetime.date.today()
    }

    return render_template("invoice.html", order=order)


# ----------------------------
# USER REGISTER
# ----------------------------

@app.route("/register",methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = connect()
        cur = conn.cursor()

        cur.execute(
        "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
        (name,email,password)
        )

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ----------------------------
# USER LOGIN
# ----------------------------

@app.route("/login",methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[3],password):
            session["user"] = user[2]
            return redirect("/store")

    return render_template("login.html")


# ----------------------------
# SERVICE CENTER
# ----------------------------

@app.route("/service",methods=["GET","POST"])
def service():

    message=""

    if request.method=="POST":

        imei = request.form["imei"]
        issue = request.form["problem"]

        conn = connect()
        cur = conn.cursor()

        cur.execute(
        "INSERT INTO service_requests(imei,issue) VALUES(%s,%s)",
        (imei,issue)
        )

        conn.commit()

        message="Service request submitted."

        cur.close()
        conn.close()

    return render_template("service.html",message=message)


# ----------------------------
# ADMIN LOGIN
# ----------------------------

@app.route("/admin",methods=["GET","POST"])
def admin():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        conn=connect()
        cur=conn.cursor()

        cur.execute("SELECT * FROM admins WHERE username=%s",(username,))
        admin=cur.fetchone()

        cur.close()
        conn.close()

        if admin and check_password_hash(admin[2],password):
            session["admin"]=username
            return redirect("/admin_dashboard")

    return render_template("admin_login.html")


# ----------------------------
# ADMIN DASHBOARD
# ----------------------------

@app.route("/admin_dashboard",methods=["GET","POST"])
def admin_dashboard():

    conn=connect()
    cur=conn.cursor()

    if request.method=="POST":

        brand=request.form["brand"]
        model=request.form["model"]
        price=request.form["price"]

        image=request.files["image"]

        filename=secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))

        cur.execute(
        "INSERT INTO products(brand,model,price,image) VALUES(%s,%s,%s,%s)",
        (brand,model,price,filename)
        )

        conn.commit()

    cur.execute("SELECT * FROM products")
    products=cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin_dashboard.html",products=products)


# ----------------------------
# DELETE PRODUCT
# ----------------------------

@app.route("/delete_product/<int:id>")
def delete_product(id):

    conn=connect()
    cur=conn.cursor()

    cur.execute("DELETE FROM products WHERE id=%s",(id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/admin_dashboard")

@app.route("/setup_db")
def setup_db():
    init_db()
    return "Database initialized"


# ----------------------------
# RUN APP
# ----------------------------

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)