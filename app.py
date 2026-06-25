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
        customers = cursor.fetchall()

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

        # ✅ total
        total = sum(item['price'] * item['quantity'] for item in cart)
        final_amount = total - discount
        due = final_amount - paid_amount

        # ✅ insert sale
        cursor.execute("""
            INSERT INTO sales (customer_id, total_amount, discount, final_amount, paid_amount, due_added)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_id, total, discount, final_amount, paid_amount, due))

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
        if due > 0:
            cursor.execute("""
                UPDATE customers SET due_amount = due_amount + ?
                WHERE id = ?
            """, (due, customer_id))

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
    cursor.execute("SELECT COUNT(*) FROM products WHERE quantity < 5")
    low_stock = cursor.fetchone()[0]

    # Total sales revenue
    cursor.execute("SELECT SUM(total_price) FROM sales")
    total_sales = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'dashboard.html',
        total_products=total_products,
        low_stock=low_stock,
        total_sales=total_sales or 0
    )

if __name__ == '__main__':
    app.run(debug=True)