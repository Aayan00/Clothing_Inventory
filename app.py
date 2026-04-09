from flask import Flask, render_template, redirect, url_for, request, flash, g, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
DATABASE = 'clothing_inventory.db'


# ---------- Database Helpers ----------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS clothing_item
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           name
                           TEXT
                           NOT
                           NULL,
                           category
                           TEXT
                           NOT
                           NULL,
                           size
                           TEXT
                           NOT
                           NULL,
                           color
                           TEXT
                           NOT
                           NULL,
                           price
                           REAL
                           NOT
                           NULL,
                           stock_quantity
                           INTEGER
                           NOT
                           NULL
                           DEFAULT
                           0
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS sale
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           item_id
                           INTEGER
                           NOT
                           NULL,
                           quantity_sold
                           INTEGER
                           NOT
                           NULL,
                           sale_date
                           TIMESTAMP
                           NOT
                           NULL,
                           total_price
                           REAL
                           NOT
                           NULL,
                           FOREIGN
                           KEY
                       (
                           item_id
                       ) REFERENCES clothing_item
                       (
                           id
                       )
                           )
                       ''')
        db.commit()


def seed_database():
    """Insert sample data if tables are empty."""
    db = get_db()
    count = db.execute('SELECT COUNT(*) FROM clothing_item').fetchone()[0]
    if count == 0:
        sample_items = [
            # Traditional
            ('Silk Saree', 'Traditional', 'M', 'Red', 2499.00, 12),
            ('Kurta Pajama', 'Traditional', 'L', 'White', 1599.00, 8),
            ('Lehenga Choli', 'Traditional', 'S', 'Pink', 4999.00, 5),
            ('Dhoti Kurta', 'Traditional', 'XL', 'Beige', 1899.00, 6),
            # Western
            ('Denim Jeans', 'Western', '32', 'Blue', 1999.00, 20),
            ('Graphic T-Shirt', 'Western', 'M', 'Black', 799.00, 25),
            ('Blazer Jacket', 'Western', 'L', 'Navy', 3499.00, 7),
            ('Summer Dress', 'Western', 'S', 'Yellow', 1299.00, 10),
            # Casual
            ('Hoodie', 'Casual', 'XL', 'Grey', 1499.00, 15),
            ('Joggers', 'Casual', 'L', 'Olive', 1299.00, 18),
            ('Polo T-Shirt', 'Casual', 'M', 'White', 899.00, 22),
            ('Sweatshirt', 'Casual', 'L', 'Maroon', 1399.00, 9),
            # Sportswear
            ('Running Shorts', 'Sportswear', 'L', 'Black', 699.00, 30),
            ('Yoga Pants', 'Sportswear', 'M', 'Purple', 999.00, 14),
            ('Tracksuit', 'Sportswear', 'XL', 'Navy', 2499.00, 6),
            # Formal
            ('Slim Fit Shirt', 'Formal', 'M', 'Light Blue', 1299.00, 16),
            ('Tailored Trousers', 'Formal', '32', 'Charcoal', 1799.00, 11),
            ('Silk Tie', 'Formal', 'One Size', 'Burgundy', 499.00, 20),
        ]
        for item in sample_items:
            db.execute('''
                       INSERT INTO clothing_item (name, category, size, color, price, stock_quantity)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ''', item)

        # Generate some random sales for demo
        item_ids = [row['id'] for row in db.execute('SELECT id FROM clothing_item').fetchall()]
        for _ in range(50):
            item_id = random.choice(item_ids)
            item = db.execute('SELECT price, stock_quantity FROM clothing_item WHERE id = ?', (item_id,)).fetchone()
            max_qty = min(item['stock_quantity'], random.randint(1, 5))
            if max_qty > 0:
                qty = random.randint(1, max_qty)
                total = item['price'] * qty
                db.execute('''
                           INSERT INTO sale (item_id, quantity_sold, sale_date, total_price)
                           VALUES (?, ?, ?, ?)
                           ''', (item_id, qty, datetime.now(), total))
                db.execute('UPDATE clothing_item SET stock_quantity = stock_quantity - ? WHERE id = ?', (qty, item_id))
        db.commit()
        print("Sample data seeded successfully.")


# ---------- Forms ----------
class ClothingItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Traditional', 'Traditional'),
        ('Western', 'Western'),
        ('Casual', 'Casual'),
        ('Sportswear', 'Sportswear'),
        ('Formal', 'Formal')
    ], validators=[DataRequired()])
    size = SelectField('Size', choices=[
        ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL')
    ], validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save')


class SaleForm(FlaskForm):
    item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
    quantity_sold = IntegerField('Quantity Sold', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Record Sale')


# ---------- Routes ----------
@app.route('/')
def index():
    db = get_db()
    items_count = db.execute('SELECT COUNT(*) FROM clothing_item').fetchone()[0]
    return render_template('index.html', items_count=items_count)


@app.route('/inventory')
def inventory():
    return render_template('inventory.html')


@app.route('/api/inventory')
def api_inventory():
    """Return inventory items as JSON for frontend filtering."""
    db = get_db()
    items = db.execute('SELECT * FROM clothing_item ORDER BY id DESC').fetchall()
    return jsonify([dict(row) for row in items])


@app.route('/inventory/add', methods=['GET', 'POST'])
def add_item():
    form = ClothingItemForm()
    if form.validate_on_submit():
        db = get_db()
        db.execute('''
                   INSERT INTO clothing_item (name, category, size, color, price, stock_quantity)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ''', (form.name.data, form.category.data, form.size.data, form.color.data,
                         form.price.data, form.stock_quantity.data))
        db.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('add_item.html', form=form)


@app.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    db = get_db()
    item = db.execute('SELECT * FROM clothing_item WHERE id = ?', (id,)).fetchone()
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('inventory'))

    form = ClothingItemForm(data=dict(item))
    if form.validate_on_submit():
        db.execute('''
                   UPDATE clothing_item
                   SET name           = ?,
                       category       = ?,
                       size           = ?,
                       color          = ?,
                       price          = ?,
                       stock_quantity = ?
                   WHERE id = ?
                   ''', (form.name.data, form.category.data, form.size.data, form.color.data,
                         form.price.data, form.stock_quantity.data, id))
        db.commit()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('edit_item.html', form=form, item=item)


@app.route('/inventory/delete/<int:id>')
def delete_item(id):
    db = get_db()
    db.execute('DELETE FROM clothing_item WHERE id = ?', (id,))
    db.commit()
    flash('Item deleted!', 'danger')
    return redirect(url_for('inventory'))


@app.route('/sale/record', methods=['GET', 'POST'])
def record_sale():
    form = SaleForm()
    db = get_db()
    items = db.execute(
        'SELECT id, name, category, size, color, stock_quantity FROM clothing_item WHERE stock_quantity > 0').fetchall()
    form.item_id.choices = [(item['id'],
                             f"{item['name']} ({item['category']}, {item['size']}, {item['color']}) - Stock: {item['stock_quantity']}")
                            for item in items]

    if form.validate_on_submit():
        item_id = form.item_id.data
        qty = form.quantity_sold.data
        item = db.execute('SELECT stock_quantity, price FROM clothing_item WHERE id = ?', (item_id,)).fetchone()
        if item['stock_quantity'] < qty:
            flash('Not enough stock!', 'danger')
            return redirect(url_for('record_sale'))

        new_stock = item['stock_quantity'] - qty
        db.execute('UPDATE clothing_item SET stock_quantity = ? WHERE id = ?', (new_stock, item_id))
        total_price = item['price'] * qty
        db.execute('''
                   INSERT INTO sale (item_id, quantity_sold, sale_date, total_price)
                   VALUES (?, ?, ?, ?)
                   ''', (item_id, qty, datetime.now(), total_price))
        db.commit()
        flash('Sale recorded successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('record_sale.html', form=form)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/dashboard_data')
def api_dashboard_data():
    db = get_db()
    sales_query = '''
                  SELECT c.id, c.name, c.category, COALESCE(SUM(s.quantity_sold), 0) as total_sold
                  FROM clothing_item c
                           LEFT JOIN sale s ON c.id = s.item_id
                  GROUP BY c.id
                  ORDER BY total_sold DESC \
                  '''
    sales_data = db.execute(sales_query).fetchall()
    items_labels = [row['name'] for row in sales_data]
    sold_quantities = [row['total_sold'] for row in sales_data]
    best_sellers = [dict(row) for row in sales_data if row['total_sold'] > 0][:5]
    worst_sellers = list(reversed([dict(row) for row in sales_data[-5:]])) if len(sales_data) >= 5 else list(
        reversed([dict(row) for row in sales_data]))
    return jsonify({
        'labels': items_labels,
        'quantities': sold_quantities,
        'best_sellers': best_sellers,
        'worst_sellers': worst_sellers
    })


# ---------- Initialize and Run ----------
if __name__ == '__main__':
    with app.app_context():
        init_db()
        seed_database()  # Add sample data if empty
    app.run(debug=True)