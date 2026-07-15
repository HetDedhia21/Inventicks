"""
One-time script to seed realistic sales history for demo/screenshot purposes.
Run this AFTER importing sample_products.csv via the Inventory page.
Safe to run only once — running it twice will double up sales and deplete stock further.
"""
import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# ---- 1. Sample customers ----
customers = [
    ("Ravi Kumar", "9820011122"),
    ("Anita Shah", "9820033344"),
    ("Meera Patel", "9820055566"),
    ("Karan Mehta", "9820077788"),
    ("Sana Sheikh", "9820099900"),
    ("Aditya Rao", "9820112233"),
]

customer_ids = []
for name, phone in customers:
    cursor.execute("SELECT id FROM customers WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    if row:
        customer_ids.append(row[0])
    else:
        cursor.execute(
            "INSERT INTO customers (name, phone, total_spent, due_amount) VALUES (?, ?, 0, 0)",
            (name, phone)
        )
        customer_ids.append(cursor.lastrowid)

conn.commit()

# ---- 2. Load products currently in inventory ----
cursor.execute("SELECT id, name, price, quantity FROM products")
products = cursor.fetchall()

if not products:
    print("No products found — import sample_products.csv first, then re-run this script.")
    conn.close()
    exit()

# Bias a few products to be clear "top sellers" for a nicer chart
popular_names = ["Notebook 200pg", "Ball Pen Blue", "USB-C Cable 1m", "Basmati Rice 5kg", "Bath Soap"]
popular = [p for p in products if p[1] in popular_names] or products[:5]
others = [p for p in products if p not in popular]

# ---- 3. Generate sales across the last 7 days (upward trend) ----
sales_per_day = [3, 4, 3, 5, 4, 6, 7]  # day -6 (oldest) to day 0 (today)
customer_due_totals = {cid: 0 for cid in customer_ids}

for day_offset, num_sales in zip(range(6, -1, -1), sales_per_day):
    sale_date = datetime.now() - timedelta(days=day_offset)

    for _ in range(num_sales):
        customer_id = random.choice(customer_ids)

        num_items = random.randint(1, 3)
        chosen_products = random.sample(
            popular if random.random() < 0.65 else products,
            k=min(num_items, len(popular if random.random() < 0.65 else products))
        )

        total = 0
        line_items = []
        for pid, pname, price, qty in chosen_products:
            cursor.execute("SELECT quantity FROM products WHERE id = ?", (pid,))
            current_qty = cursor.fetchone()[0]
            if current_qty <= 0:
                continue
            sell_qty = min(random.randint(1, 3), current_qty)
            if sell_qty <= 0:
                continue
            total += price * sell_qty
            line_items.append((pid, sell_qty, price))

        if not line_items:
            continue

        discount = round(total * random.choice([0, 0, 0, 0.05, 0.1]), 2)
        final_amount = round(total - discount, 2)

        if random.random() < 0.8:
            paid_amount = final_amount
        else:
            paid_amount = round(final_amount * random.choice([0.4, 0.6, 0.7]), 2)

        old_due = customer_due_totals[customer_id]
        new_due = round(old_due + final_amount - paid_amount, 2)
        customer_due_totals[customer_id] = new_due

        cursor.execute("""
            INSERT INTO sales (customer_id, total_amount, discount, final_amount, paid_amount, due_added, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (customer_id, total, discount, final_amount, paid_amount, new_due,
              sale_date.strftime('%Y-%m-%d %H:%M:%S')))

        sale_id = cursor.lastrowid

        for pid, sell_qty, price in line_items:
            cursor.execute(
                "INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (sale_id, pid, sell_qty, price)
            )
            cursor.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                (sell_qty, pid)
            )

# ---- 4. Apply final due amounts to customers ----
for cid, due in customer_due_totals.items():
    cursor.execute("UPDATE customers SET due_amount = ? WHERE id = ?", (due, cid))

conn.commit()
conn.close()

print("Seed data created: customers, 7 days of sales, and sale items.")
print("Refresh your Dashboard — trend chart, top products, and dues should now be populated.")
