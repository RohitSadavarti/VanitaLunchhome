from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os # Import the 'os' module to access environment variables

# The Flask app must be named 'app' for Vercel to detect it
app = Flask(__name__)
CORS(app)

# --- MODIFIED: Use Environment Variables for Database Configuration ---
# This is more secure and necessary for deployment.
# You will set these variables in the Vercel dashboard.
DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'database': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'port': os.environ.get('DB_PORT', '5432') # Default to 5432 if not set
}

def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

# --- API Routes ---

# MODIFIED: This route serves your frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the main HTML file for the root path."""
    if path == "":
        # We need to adjust the path to find index.html from inside the 'api' folder
        return send_from_directory('../customer/template', 'index.html')
    else:
        # This can be used to serve other static files if needed, otherwise return 404
        return "Not Found", 404


@app.route('/api/menu-items')
def get_menu_items():
    """Get all menu items, grouped by category."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, name, description, price, image_url, category FROM menu_items ORDER BY category, name')
        items = cursor.fetchall()
        
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
            'categories': categories
        })
        
    except psycopg2.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order by adding entries for each item."""
    data = request.get_json()
    
    if not all(key in data for key in ['customer_name', 'mobile_number', 'items']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        for item in data['items']:
            final_price = float(item['price']) * int(item['quantity'])
            
            cursor.execute('''
                INSERT INTO orders (customer_name, mobile_number, item, unit, final_price)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                data['customer_name'],
                data['mobile_number'],
                item['name'],
                item['quantity'],
                final_price
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Order placed successfully!'
        }), 201
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# REMOVED: The init_database() and app.run() block.
# Vercel handles running the app, and you should manage your database schema separately (e.g., using a migration tool or connecting directly).
