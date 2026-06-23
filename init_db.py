import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Products Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    created_at DATETIME DEFAULT (datetime('now','localtime')),
    updated_at DATETIME DEFAULT (datetime('now','localtime')) 
)
''')

# Sales Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    total_amount REAL,
    discount REAL,
    final_amount REAL,
    paid_amount REAL,
    due_added REAL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

#Sale Items Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price REAL
)
''')

# Customers Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT UNIQUE,
    total_spent REAL DEFAULT 0,
    due_amount REAL DEFAULT 0
)
''')

conn.commit()
conn.close()

print("Database initialized!")