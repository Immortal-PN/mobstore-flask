from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ----------------------------
# DATABASE CONNECTION
# ----------------------------

def connect():
    database_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(database_url)


# ----------------------------
# LANDING PAGE
# ----------------------------

@app.route("/")
def home():
    return render_template("landing.html")


# ----------------------------
# ADMIN LOGIN
# ----------------------------

@app.route("/admin", methods=["GET","POST"])
def admin():

    error = None

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT username,password FROM admins WHERE username=%s",
            (username,)
        )

        admin = cur.fetchone()

        cur.close()
        conn.close()

        if admin:

            if check_password_hash(admin[1], password):

                session["admin"] = admin[0]

                return redirect("/admin_dashboard")

        error = "Invalid username or password"

    return render_template("admin_login.html", error=error)


# ----------------------------
# ADMIN DASHBOARD
# ----------------------------

@app.route("/admin_dashboard", methods=["GET","POST"])
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin")

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
# LOGOUT
# ----------------------------

@app.route("/admin_logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin")


# ----------------------------
# DELETE PRODUCT
# ----------------------------

@app.route("/delete_product/<int:id>")
def delete_product(id):

    if "admin" not in session:
        return redirect("/admin")

    conn = connect()
    cur = conn.cursor()

    cur.execute("DELETE FROM products WHERE id=%s",(id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/admin_dashboard")


# ----------------------------
# RUN APP
# ----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)