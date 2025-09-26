from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'vanita_lunch_home',
    'user': 'your_username',
    'password': 'your_password',
    'port': '5432'
}

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create menu_items table with categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                image_url TEXT,
                category VARCHAR(100) DEFAULT 'Main Course',
                is_available BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(255) NOT NULL,
                mobile_number VARCHAR(15) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create order_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id),
                menu_item_id INTEGER REFERENCES menu_items(id),
                quantity INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL
            )
        ''')
        
        # Insert sample data if menu_items table is empty
        cursor.execute('SELECT COUNT(*) FROM menu_items')
        count = cursor.fetchone()[0]
        
        if count == 0:
            sample_items = [
                ('Special Thali', 'A complete meal with 2 sabzis, dal, rice, roti, salad, and sweet.', 150.00, 'https://placehold.co/600x400/f97316/ffffff?text=Special+Thali', 'Thali'),
                ('Paneer Butter Masala', 'Creamy paneer in a rich tomato and butter gravy.', 180.00, 'https://placehold.co/600x400/ea580c/ffffff?text=Paneer+Masala', 'Main Course'),
                ('Dal Tadka', 'Yellow lentils tempered with ghee and spices.', 120.00, 'https://placehold.co/600x400/d97706/ffffff?text=Dal+Tadka', 'Dal & Curry'),
                ('Jeera Rice', 'Basmati rice flavored with cumin seeds.', 90.00, 'https://placehold.co/600x400/b45309/ffffff?text=Jeera+Rice', 'Rice & Biryani'),
                ('Tandoori Roti', 'Whole wheat bread cooked in a tandoor.', 20.00, 'https://placehold.co/600x400/92400e/ffffff?text=Tandoori+Roti', 'Bread'),
                ('Masala Chaas', 'Spiced buttermilk, a refreshing digestive drink.', 40.00, 'https://placehold.co/600x400/78350f/ffffff?text=Masala+Chaas', 'Beverages'),
                ('Chole Bhature', 'Spicy chickpea curry served with fried bread.', 140.00, 'https://placehold.co/600x400/f59e0b/ffffff?text=Chole+Bhature', 'Main Course'),
                ('Rajma Rice', 'Kidney bean curry served with steamed rice.', 130.00, 'https://placehold.co/600x400/ef4444/ffffff?text=Rajma+Rice', 'Main Course'),
                ('Mango Lassi', 'Sweet yogurt drink with mango pulp.', 60.00, 'https://placehold.co/600x400/fbbf24/ffffff?text=Mango+Lassi', 'Beverages'),
                ('Gulab Jamun', 'Sweet milk dumplings in sugar syrup.', 80.00, 'https://placehold.co/600x400/f472b6/ffffff?text=Gulab+Jamun', 'Desserts')
            ]
            
            cursor.executemany('''
                INSERT INTO menu_items (name, description, price, image_url, category)
                VALUES (%s, %s, %s, %s, %s)
            ''', sample_items)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"Database initialization error: {e}")
        if conn:
            conn.rollback()
            cursor.close()
            conn.close()
        return False

# API Routes

@app.route('/')
def serve_frontend():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/api/menu-items')
def get_menu_items():
    """Get all menu items grouped by category"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, name, description, price, image_url, category, is_available
            FROM menu_items 
            WHERE is_available = true
            ORDER BY category, name
        ''')
        
        items = cursor.fetchall()
        
        # Group items by category
        categories = {}
        for item in items:
            category = item['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(dict(item))
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'categories': categories,
            'total_items': len(items)
        })
        
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/menu-items/<int:item_id>')
def get_menu_item(item_id):
    """Get a specific menu item"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, name, description, price, image_url, category, is_available
            FROM menu_items 
            WHERE id = %s
        ''', (item_id,))
        
        item = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if item:
            return jsonify({'success': True, 'item': dict(item)})
        else:
            return jsonify({'error': 'Item not found'}), 404
            
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/menu-items', methods=['POST'])
def add_menu_item():
    """Add a new menu item"""
    data = request.get_json()
    
    if not all(key in data for key in ['name', 'description', 'price', 'category']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            INSERT INTO menu_items (name, description, price, image_url, category)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, description, price, image_url, category, is_available
        ''', (
            data['name'],
            data['description'],
            float(data['price']),
            data.get('image_url', ''),
            data['category']
        ))
        
        new_item = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'item': dict(new_item)}), 201
        
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/menu-items/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    """Delete a menu item"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM menu_items WHERE id = %s', (item_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Item deleted successfully'})
        else:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Item not found'}), 404
            
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    data = request.get_json()
    
    if not all(key in data for key in ['customer_name', 'mobile_number', 'items', 'total_amount']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Create order
        cursor.execute('''
            INSERT INTO orders (customer_name, mobile_number, total_amount)
            VALUES (%s, %s, %s)
            RETURNING id, created_at
        ''', (
            data['customer_name'],
            data['mobile_number'],
            float(data['total_amount'])
        ))
        
        order = cursor.fetchone()
        order_id = order['id']
        
        # Add order items
        for item in data['items']:
            cursor.execute('''
                INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            ''', (
                order_id,
                item['id'],
                item['quantity'],
                float(item['price'])
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'message': 'Order placed successfully!'
        }), 201
        
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/orders')
def get_orders():
    """Get all orders with items"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT o.id, o.customer_name, o.mobile_number, o.total_amount, 
                   o.status, o.created_at,
                   oi.quantity, oi.price as item_price,
                   mi.name as item_name
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE o.status = 'pending'
            ORDER BY o.created_at DESC
        ''')
        
        rows = cursor.fetchall()
        
        # Group by order
        orders = {}
        for row in rows:
            order_id = row['id']
            if order_id not in orders:
                orders[order_id] = {
                    'id': row['id'],
                    'customer_name': row['customer_name'],
                    'mobile_number': row['mobile_number'],
                    'total_amount': float(row['total_amount']),
                    'status': row['status'],
                    'created_at': row['created_at'].isoformat(),
                    'items': []
                }
            
            if row['item_name']:
                orders[order_id]['items'].append({
                    'name': row['item_name'],
                    'quantity': row['quantity'],
                    'price': float(row['item_price'])
                })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'orders': list(orders.values())
        })
        
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/orders/<int:order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    """Mark an order as completed"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders SET status = 'completed' WHERE id = %s
        ''', (order_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Order completed successfully'})
        else:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Order not found'}), 404
            
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/categories')
def get_categories():
    """Get all unique categories"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT category FROM menu_items 
            WHERE is_available = true 
            ORDER BY category
        ''')
        
        categories = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

if __name__ == '__main__':
    print("Initializing database...")
    if init_database():
        print("Database initialized successfully!")
        print("Starting server...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to initialize database. Please check your PostgreSQL configuration.")
