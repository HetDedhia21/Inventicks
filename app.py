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

@app.route('/sales')
def sales():
    return render_template('sales.html')

if __name__ == '__main__':
    app.run(debug=True)