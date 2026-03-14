import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()


# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
email TEXT UNIQUE NOT NULL,
password TEXT NOT NULL
)
""")


# PRODUCTS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
brand TEXT NOT NULL,
model TEXT NOT NULL,
price INTEGER NOT NULL,
image TEXT
)
""")


# ORDERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product_id INTEGER,
imei TEXT UNIQUE,
purchase_date TEXT,
warranty_expiry TEXT
)
""")


# SERVICE REQUESTS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS service_requests(
id INTEGER PRIMARY KEY AUTOINCREMENT,
imei TEXT,
problem TEXT,
request_date TEXT
)
""")


conn.commit()
conn.close()

print("Database and tables created successfully.")