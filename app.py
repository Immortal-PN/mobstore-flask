from flask import Flask, render_template, request, redirect, session
import base64
import psycopg2
import os
import random
import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================
# DATABASE CONNECTION
# ==============================

def connect():
    return psycopg2.connect(os.environ["DATABASE_URL"])



# ==============================
# IMEI GENERATOR
# ==============================

def generate_imei():
    return str(random.randint(100000000000000,999999999999999))


# ==============================
# LANDING
# ==============================

@app.route("/")
def landing():
    return render_template("landing.html")


# ==============================
# STORE
# ==============================

@app.route("/store")
def store():

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products ORDER BY id DESC")
    products = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("home.html",products=products)



@app.route("/service", methods=["GET","POST"])
def service():

    message = ""

    if request.method == "POST":

        imei = request.form.get("imei")
        issue = request.form.get("problem")

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO service_requests
        (imei, issue, status, created_at)
        VALUES (%s,%s,%s,%s)
        """,(imei,issue,"Pending",datetime.datetime.now()))

        conn.commit()

        cur.close()
        conn.close()

        message = "Service request submitted successfully."

    return render_template("service.html", message=message)




# ==============================
# PRODUCT
# ==============================

@app.route("/product/<int:id>")
def product(id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id=%s",(id,))
    product = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("product.html",product=product)


# ==============================
# ADD TO CART
# ==============================

@app.route("/add_to_cart/<int:id>")
def add_to_cart(id):

    if "user_id" not in session:
        return redirect("/login")

    user_id=session["user_id"]

    conn=connect()
    cur=conn.cursor()

    cur.execute(
        "SELECT id,quantity FROM cart WHERE user_id=%s AND product_id=%s",
        (user_id,id)
    )

    item=cur.fetchone()

    if item:
        cur.execute(
            "UPDATE cart SET quantity=quantity+1 WHERE id=%s",
            (item[0],)
        )
    else:
        cur.execute(
            "INSERT INTO cart(user_id,product_id,quantity) VALUES(%s,%s,%s)",
            (user_id,id,1)
        )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/cart")


# ==============================
# CART
# ==============================

@app.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect("/login")

    user_id=session["user_id"]

    conn=connect()
    cur=conn.cursor()

    cur.execute("""
        SELECT products.id,products.brand,products.model,products.price,products.image_data,cart.quantity
        FROM cart
        JOIN products ON cart.product_id=products.id
        WHERE cart.user_id=%s
        """,(user_id,))

    rows=cur.fetchall()

    items=[]
    total=0

    for r in rows:

        subtotal=r[3]*r[5]
        total+=subtotal

        items.append({
        "id": r[0],
        "brand": r[1],
        "model": r[2],
        "price": r[3],
        "image_data": r[4],
        "qty": r[5],
        "subtotal": subtotal
        })

    cur.close()
    conn.close()

    return render_template("cart.html",items=items,total=total)


# ==============================
# REMOVE CART ITEM
# ==============================

@app.route("/remove_cart/<int:id>")
def remove_cart(id):

    user_id=session["user_id"]

    conn=connect()
    cur=conn.cursor()

    cur.execute(
        "DELETE FROM cart WHERE user_id=%s AND product_id=%s",
        (user_id,id)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/cart")


# ==============================
# CHECKOUT
# ==============================

@app.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect("/login")

    user_email = session["user_email"]

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT products.id, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = %s
    """, (session["user_id"],))

    items = cur.fetchall()

    if not items:
        return redirect("/cart")

    total = 0

    generated_imei = None

    for item in items:

        product_id = item[0]
        price = item[1]
        qty = item[2]

        total = price * qty

    imei = generate_imei()
    generated_imei = imei

    cur.execute("""
        INSERT INTO orders
        (user_email, product_id, quantity, total_price, imei, order_date)
        VALUES (%s,%s,%s,%s,%s,%s)
    """,(user_email,product_id,qty,total,imei,datetime.datetime.now()))

    # clear cart
    cur.execute(
        "DELETE FROM cart WHERE user_id=%s",
        (session["user_id"],)
    )

    conn.commit()

    cur.close()
    conn.close()

    order = {
    "date": datetime.date.today(),
    "total": total,
    "imei": generated_imei
    }

    return render_template("invoice.html", order=order)


# ==============================
# LOGIN
# ==============================

@app.route("/login",methods=["GET","POST"])
def login():

    error=None

    if request.method=="POST":

        email=request.form["email"]
        password=request.form["password"]

        conn=connect()
        cur=conn.cursor()

        cur.execute(
            "SELECT id,email,password FROM users WHERE email=%s",
            (email,)
        )

        user=cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[2],password):

            session["user_id"]=user[0]
            session["user_email"]=user[1]

            return redirect("/store")

        error="Invalid login credentials"

    return render_template("login.html",error=error)


# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


# ==============================
# ADMIN LOGIN
# ==============================

@app.route("/admin",methods=["GET","POST"])
def admin():

    error=None

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        conn=connect()
        cur=conn.cursor()

        cur.execute(
            "SELECT username,password FROM admins WHERE username=%s",
            (username,)
        )

        admin=cur.fetchone()

        cur.close()
        conn.close()

        if admin and check_password_hash(admin[1],password):

            session["admin"]=admin[0]
            return redirect("/admin_dashboard")

        error="Invalid credentials"

    return render_template("admin_login.html",error=error)


# ==============================
# ADMIN DASHBOARD
# ==============================

@app.route("/admin_dashboard",methods=["GET","POST"])
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin")

    conn=connect()
    cur=conn.cursor()

    if request.method=="POST":

        brand=request.form["brand"]
        model=request.form["model"]
        price=request.form["price"]
        ram=request.form["ram"]
        storage=request.form["storage"]
        battery=request.form["battery"]
        category=request.form["category"]

        image = request.files["image"]
        image_data = None

        if image and image.filename != "":
            image_bytes = image.read()
            image_data = base64.b64encode(image_bytes).decode("utf-8")

        cur.execute("""
        INSERT INTO products
        (brand,model,price,image_data,ram,storage,battery,category)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """,(brand,model,price,image_data,ram,storage,battery,category))

        conn.commit()

    cur.execute("SELECT * FROM products ORDER BY id DESC")
    products=cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM users")
    users=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    orders=cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total_price),0) FROM orders")
    revenue=cur.fetchone()[0]

    cur.close()
    conn.close()

    stats={
        "users":users,
        "orders":orders,
        "revenue":revenue
    }

    return render_template("admin_dashboard.html",products=products,stats=stats)


# ==============================
# DELETE PRODUCT
# ==============================

@app.route("/delete_product/<int:id>")
def delete_product(id):

    if "admin" not in session:
        return redirect("/admin")

    conn=connect()
    cur=conn.cursor()

    cur.execute("DELETE FROM products WHERE id=%s",(id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/admin_dashboard")


if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)