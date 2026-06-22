from flask import Flask, render_template, request, redirect, url_for    
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
    conn = get_db_connection()
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
        return redirect('/inventory')

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

    conn.close()
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
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    message = ""

    # ✅ Always fetch products & customers (IMPORTANT FIX)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT id, name, phone FROM customers")
    customers = cursor.fetchall()

    # ✅ Fetch sales history
    cursor.execute('''
        SELECT sales.id, products.name, sales.quantity_sold, sales.total_price, sales.date
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.date DESC
    ''')
    sales = cursor.fetchall()

    selected_customer = None
    customer_history = []
    customer_id = None

    if request.method == 'POST':

        customer_type = request.form.get('customer_type')

        # ✅ HANDLE NEW CUSTOMER
        if customer_type == 'new':
            name = request.form.get('new_name')
            phone = request.form.get('new_phone')

            if not name or not phone:
                message = "Enter customer name & phone"
            else:
                cursor.execute(
                    "INSERT INTO customers (name, phone, total_spent, due_amount) VALUES (?, ?, 0, 0)",
                    (name, phone)
                )
                conn.commit()
                customer_id = cursor.lastrowid

        # ✅ HANDLE EXISTING CUSTOMER
        elif customer_type == 'existing':
            customer_id = request.form.get('existing_customer')

            if not customer_id:
                message = "Select a customer"

            else:
                # Get customer details
                cursor.execute(
                    "SELECT id, name, total_spent, due_amount FROM customers WHERE id=?",
                    (customer_id,)
                )
                selected_customer = cursor.fetchone()

                # Get customer history
                cursor.execute('''
                    SELECT products.name, sales.quantity_sold, sales.total_price, sales.date
                    FROM sales
                    JOIN products ON sales.product_id = products.id
                    WHERE sales.customer_id = ?
                    ORDER BY sales.date DESC
                ''', (customer_id,))
                customer_history = cursor.fetchall()

        # ✅ HANDLE SALE SUBMISSION
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')

        if product_id and quantity:
            try:
                quantity = int(quantity)

                if quantity <= 0:
                    message = "Quantity must be positive"

                else:
                    # Get product details
                    cursor.execute(
                        "SELECT name, price, quantity FROM products WHERE id=?",
                        (product_id,)
                    )
                    product = cursor.fetchone()

                    if not product:
                        message = "Product not found"

                    elif product[2] < quantity:
                        message = "Not enough stock"

                    else:
                        total_price = product[1] * quantity
                        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # Insert sale
                        cursor.execute('''
                            INSERT INTO sales (product_id, quantity_sold, total_price, date, customer_id)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (product_id, quantity, total_price, date, customer_id))

                        # Update stock
                        cursor.execute(
                            "UPDATE products SET quantity = quantity - ? WHERE id=?",
                            (quantity, product_id)
                        )

                        # Update customer spending
                        cursor.execute(
                            "UPDATE customers SET total_spent = total_spent + ? WHERE id=?",
                            (total_price, customer_id)
                        )

                        conn.commit()

                        message = "Sale successful!"

                        return redirect(url_for('sales'))

            except ValueError:
                message = "Invalid quantity"

    conn.close()

    return render_template(
        'sales.html',
        products=products,
        customers=customers,  # ✅ THIS FIXES YOUR ERROR
        sales=sales,
        message=message,
        selected_customer=selected_customer,
        customer_history=customer_history
    )

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