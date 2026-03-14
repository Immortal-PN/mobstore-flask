import psycopg2
import os

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id SERIAL PRIMARY KEY,
name TEXT,
email TEXT,
password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products(
id SERIAL PRIMARY KEY,
brand TEXT,
model TEXT,
price INTEGER,
image TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
id SERIAL PRIMARY KEY,
product_id INTEGER,
imei TEXT,
purchase_date TEXT,
warranty_expiry TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS service_requests(
id SERIAL PRIMARY KEY,
imei TEXT,
problem TEXT,
request_date TEXT
)
""")

conn.commit()
conn.close()

print("Tables created successfully")