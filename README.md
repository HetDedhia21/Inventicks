# 📦 Inventicks

**A lightweight Inventory & Billing Management System for small businesses — built with Flask, SQLite, and Chart.js.**

Track products, record sales, manage customer dues, and get real insights through a clean, business-agnostic dashboard. Configurable for any type of shop — grocery, stationery, electronics, or anything else.

![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=flat&logo=sqlite&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=flat&logo=chart.js&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 📋 Overview

Inventicks is a full-stack inventory and billing platform designed to help small businesses manage stock, record sales, and understand their operations at a glance — without being locked into one industry. A single settings page lets any business configure its name, type, and low-stock threshold, so the same codebase works whether you're running a kirana store or an electronics shop.

---

## ✨ Features

- 📦 Add, edit, and track products with quantity, category, and unit
- 🧾 Record sales with multi-item carts, discounts, and partial payments
- 👤 Customer tracking with running due/credit balances
- 📊 Live dashboard — revenue, sales count, product count, customer count
- 📈 7-day sales trend chart (Chart.js)
- 🏆 Top-selling products, ranked by units sold
- ⚠️ Configurable low-stock alerts
- 🕒 Recent sales activity feed
- 📥 Bulk product import via CSV
- ⚙️ Business settings — name, type, currency symbol, stock threshold
- 🎨 Clean sidebar dashboard UI with a custom ink/ochre theme
- 🗄️ Persistent SQLite storage — no external DB required

---

## 🛠️ Tech Stack

**Backend:** Flask, SQLite, Jinja2
**Frontend:** HTML, CSS (custom, no framework), Chart.js
**Tools:** DB Browser for SQLite

---

## 📁 Project Structure

```
Inventicks/
├── app.py                 # Flask routes & business logic
├── init_db.py              # Database schema + seed settings
├── database.db              # SQLite database
├── requirements.txt
├── static/
│   └── style.css            # Sidebar layout, ink/ochre/cream theme
├── templates/
│   ├── base.html              # Shared sidebar layout
│   ├── index.html
│   ├── inventory.html
│   ├── sales.html
│   ├── edit_product.html
│   ├── dashboard.html
│   └── settings.html
└── uploads/                 # CSV import staging
```

---

## 🚀 Getting Started

### Prerequisites
- Python ≥ 3.10
- pip

### 1. Clone
```bash
git clone https://github.com/HetDedhia21/Inventicks.git
cd Inventicks
```

### 2. Install & initialize
```bash
pip install -r requirements.txt
python init_db.py
```

### 3. Run
```bash
python app.py
```
Visit `http://localhost:5000`.

---

## ⚙️ Configuration

All business-level settings (name, business type, low-stock threshold, currency symbol) are managed in-app under **Settings** — no `.env` file needed for a single-instance deployment.

---

## ☁️ Deployment

Recommended: **PythonAnywhere** — Flask + SQLite need real persistent disk, which serverless platforms (Vercel, etc.) don't provide.

1. Clone the repo into your PythonAnywhere console
2. Create a virtualenv, `pip install -r requirements.txt`
3. Run `python init_db.py` to set up the database
4. Configure a manual Flask web app pointing at `app.py`
5. Set the working directory to the project folder
6. Map `/static/` to the `static/` directory
7. Reload

---

## 🚧 Challenges

Designing a schema generic enough to fit any business type without losing the specificity that makes low-stock alerts and analytics useful; building trend and top-product analytics directly from transactional data; migrating an existing SQLite database safely without losing data.

## 📊 What I Learned

- Structuring Flask apps for multi-tenant-style configurability
- Writing SQL aggregation queries for dashboard analytics (trends, top products)
- Designing a UI system (sidebar layout, reusable base template) in plain Jinja2 + CSS
- Deploying Flask + SQLite correctly on a host with real persistent storage
- Practical Git/GitHub auth workflows (PATs) for deployment

---

## 🤝 Contributing

Pull requests are welcome — please open an issue first for major changes.

## 📄 License

MIT
