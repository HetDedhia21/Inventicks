from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

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
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form['quantity']

        cursor.execute(
            "INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
            (name, price, quantity)
        )
        conn.commit()

    # FETCH PRODUCTS
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

        conn.commit()
        conn.close()
        return redirect('/inventory')

    product = cursor.execute(
        "SELECT * FROM products WHERE id = ?", (id,)
    ).fetchone()
    conn.close()

    return render_template('edit_product.html', product=product)

@app.route('/sales')
def sales():
    return "Sales Page"

@app.route('/dashboard')
def dashboard():
    return "Dashboard Page"

if __name__ == '__main__':
    app.run(debug=True)