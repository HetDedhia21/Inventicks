import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Products Table (generic fields work for any business type)
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    category TEXT DEFAULT '',
    unit TEXT DEFAULT 'pcs',
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

# Sale Items Table
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

# Settings Table - single row, makes the platform business-agnostic
cursor.execute('''
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    business_name TEXT DEFAULT 'My Business',
    business_type TEXT DEFAULT 'General Store',
    low_stock_threshold INTEGER DEFAULT 5,
    currency_symbol TEXT DEFAULT '₹'
)
''')

cursor.execute("SELECT COUNT(*) FROM settings")
if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO settings (id, business_name, business_type, low_stock_threshold, currency_symbol) "
        "VALUES (1, 'My Business', 'General Store', 5, '₹')"
    )

conn.commit()
conn.close()

print("Database initialized!")
