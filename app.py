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

@app.route('/sales')
def sales():
    return "Sales Page"

@app.route('/dashboard')
def dashboard():
    return "Dashboard Page"

if __name__ == '__main__':
    app.run(debug=True)