from flask import Flask, render_template, request, redirect
import sqlite3
from flask import flash

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

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form['quantity']

        cursor.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
            (name, price, quantity)
        )
        conn.commit()
        conn.close()

        flash("Product added successfully!")

        return redirect('/inventory')   

    products = cursor.execute("SELECT * FROM products").fetchall()
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
            SET name = ?, price = ?, quantity = ?
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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    message = ""

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity_sold = int(request.form['quantity'])

        # Get product details
        cursor.execute("SELECT name, quantity, price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        name, current_quantity, price = product

        # 🚨 VALIDATION
        if quantity_sold > current_quantity:
            message = "❌ Not enough stock!"
        else:
            # Update product quantity
            new_quantity = current_quantity - quantity_sold
            cursor.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, product_id))

            # Save sale
            total_price = quantity_sold * price
            cursor.execute(
                "INSERT INTO sales (product_id, quantity_sold, total_price) VALUES (?, ?, ?)",
                (product_id, quantity_sold, total_price)
            )

            conn.commit()
            message = "✅ Sale recorded successfully!"

    # Fetch products
    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()

    conn.close()

    return render_template('sales.html', products=products, message=message)

@app.route('/sales-history')
def sales_history():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT products.name, sales.quantity_sold, sales.total_price, sales.date
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.date DESC
    ''')

    sales = cursor.fetchall()
    conn.close()

    return render_template('sales_history.html', sales=sales)

if __name__ == '__main__':
    app.run(debug=True)