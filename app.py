from flask import Flask, render_template, request, redirect, url_for, jsonify  
import sqlite3
from flask import flash
import csv
import os
from datetime import datetime

app = Flask(__name__)

app.secret_key = "inventicks_secret"

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ADD PRODUCT
        if request.method == 'POST' and 'name' in request.form:
            name = request.form['name']
            price = request.form['price']
            quantity = request.form['quantity']

            cursor.execute(
                "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
                (name, price, quantity)
            )
            conn.commit()

            flash("Product added successfully!")
            return redirect('/inventory')   # ✅ safe now

        # SEARCH + FILTER
        search = request.args.get('search')
        filter_type = request.args.get('filter')

        query = "SELECT * FROM products WHERE 1=1"
        params = []

        if search:
            query += " AND name LIKE ?"
            params.append('%' + search + '%')

        if filter_type == 'low':
            query += " AND quantity < 10"
        elif filter_type == 'out':
            query += " AND quantity = 0"

        products = cursor.execute(query, params).fetchall()

    return render_template('inventory.html', products=products)

@app.route('/delete/<int:id>')
def delete_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash("Product deleted successfully!")

    return redirect('/inventory')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form['quantity']

        cursor.execute("""
            UPDATE products
            SET name = ?, 
                price = ?, 
                quantity = ?, 
                updated_at = datetime('now','localtime')
            WHERE id = ?
        """, (name, price, quantity, id))

        flash("Product updated successfully!")

        conn.commit()
        conn.close()
        return redirect('/inventory')

    product = cursor.execute(
        "SELECT * FROM products WHERE id = ?", (id,)
    ).fetchone()
    conn.close()

    return render_template('edit_product.html', product=product)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']

    if not file:
        flash("No file selected")
        return redirect('/inventory')

    filepath = os.path.join('uploads', file.filename)

    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    file.save(filepath)

    conn = get_db_connection()
    cursor = conn.cursor()

    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        
        header = next(reader)

        # VALIDATE HEADER
        expected_header = ['name', 'quantity', 'price']
        if [h.strip().lower() for h in header] != expected_header:
            flash("Invalid CSV format! Required: name, quantity, price")
            return redirect('/inventory')

        for row in reader:
            # VALIDATE ROW LENGTH
            if len(row) != 3:
                continue  # skip bad rows

            name, quantity, price = row

            cursor.execute(
                "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
                (name, price, quantity)
            )

        max_rows = 100  # safety limit
    count = 0

    for row in reader:
        if count >= max_rows:
            break

        if len(row) != 3:
            continue

        name, quantity, price = row

        cursor.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
            (name, price, quantity)
        )

        count += 1

    conn.commit()
    conn.close()

    flash("CSV uploaded successfully!")
    flash(f"{count} products uploaded successfully!")
    return redirect('/inventory')

@app.route('/delete_all')
def delete_all():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products")

    conn.commit()
    conn.close()

    flash("All products deleted!")
    return redirect('/inventory')

@app.route('/sales', methods=['GET', 'POST'])
def sales():

    if request.method == 'GET':
        # show page
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        cursor.execute("SELECT * FROM customers")
        rows = cursor.fetchall()

        customers = [
            {
                "id": r[0],
                "name": r[1],
                "phone": r[2],
                "due_amount": r[4]
            }
            for r in rows
        ]
        conn.close()

        return render_template('sales.html', products=products, customers=customers)

    elif request.method == 'POST':
        data = request.get_json()

        phone = data.get('phone')
        name = data.get('name')
        cart = data.get('cart')
        discount = float(data.get('discount', 0))
        paid_amount = float(data.get('paid_amount', 0))

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # ✅ check customer
        cursor.execute("SELECT id FROM customers WHERE phone = ?", (phone,))
        customer = cursor.fetchone()

        if customer:
            customer_id = customer[0]
        else:
            cursor.execute(
                "INSERT INTO customers (name, phone, due_amount) VALUES (?, ?, 0)",
                (name, phone)
            )
            customer_id = cursor.lastrowid

        # get old due first
        cursor.execute("SELECT due_amount FROM customers WHERE id = ?", (customer_id,))
        old_due = cursor.fetchone()[0]

        total = sum(item['price'] * item['quantity'] for item in cart)
        final_amount = total - discount

        # ✅ NEW LOGIC
        new_due = old_due + final_amount - paid_amount

        # ✅ insert sale
        cursor.execute("""
            INSERT INTO sales (customer_id, total_amount, discount, final_amount, paid_amount, due_added)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_id, total, discount, final_amount, paid_amount, new_due))

        sale_id = cursor.lastrowid

        # ✅ items + stock update
        for item in cart:
            cursor.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (sale_id, item['id'], item['quantity'], item['price']))

            cursor.execute("""
                UPDATE products SET quantity = quantity - ?
                WHERE id = ?
            """, (item['quantity'], item['id']))

        # ✅ update due
        cursor.execute("""
            UPDATE customers SET due_amount = ?
            WHERE id = ?
        """, (new_due, customer_id))

        conn.commit()
        conn.close()

        return jsonify({"message": "Sale completed"})

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    # Low stock (example: quantity < 5)
    cursor.execute("SELECT name, quantity FROM products WHERE quantity < 5 LIMIT 5")
    low_stock_items = cursor.fetchall()

   # Total revenue
    cursor.execute("SELECT SUM(final_amount) FROM sales")
    total_revenue = cursor.fetchone()[0] or 0

    # Total sales count
    cursor.execute("SELECT COUNT(*) FROM sales")
    total_sales_count = cursor.fetchone()[0]

    # Total customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    # Recent Sales
    cursor.execute("SELECT id, final_amount, date FROM sales ORDER BY date DESC LIMIT 5")
    recent_sales = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total_products=total_products,
        low_stock_items=low_stock_items,
        total_revenue=total_revenue,
        total_sales_count=total_sales_count,
        total_customers=total_customers,
        recent_sales=recent_sales
    )

if __name__ == '__main__':
    app.run(debug=True)