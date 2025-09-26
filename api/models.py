# app/models.py
from . import db
from datetime import datetime
from sqlalchemy import func

class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    veg_nonveg = db.Column(db.String(20))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False, default="Walk-in")
    customer_mobile = db.Column(db.String(15))
    items = db.Column(db.JSON, nullable=False)  # Store items as JSON
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Preparing')
    payment_method = db.Column(db.String(50), nullable=False, default='Cash')
    payment_id = db.Column(db.String(100))  # For Razorpay transaction ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# app/routes.py
from flask import request, jsonify, Blueprint
from . import db, socketio
from .models import MenuItem, Order
from datetime import datetime, date
import json

bp = Blueprint('api', __name__)

# --- API Routes ---

@bp.route('/api/menu', methods=['GET'])
def get_menu():
    """
    Get all available menu items
    """
    try:
        menu_items = MenuItem.query.filter_by(is_available=True).all()
        return jsonify([item.to_dict() for item in menu_items])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/orders', methods=['GET'])
def get_orders():
    """
    Get all orders, optionally filtered by date or status
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        date_filter = request.args.get('date')
        limit = request.args.get('limit', 50, type=int)
        
        query = Order.query
        
        # Apply filters
        if status:
            query = query.filter(Order.status == status)
            
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(func.date(Order.created_at) == filter_date)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        # Order by newest first and limit results
        orders = query.order_by(Order.created_at.desc()).limit(limit).all()
        
        return jsonify([order.to_dict() for order in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/orders', methods=['POST'])
def create_order():
    """
    Create a new order
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('items'):
            return jsonify({'error': 'Items are required'}), 400
        if not data.get('total_price'):
            return jsonify({'error': 'Total price is required'}), 400
        if not data.get('customer_name'):
            return jsonify({'error': 'Customer name is required'}), 400
        if not data.get('customer_mobile'):
            return jsonify({'error': 'Customer mobile is required'}), 400
        
        # Create new order
        new_order = Order(
            customer_name=data['customer_name'],
            customer_mobile=data['customer_mobile'],
            items=data['items'],
            subtotal=data.get('subtotal', data['total_price']),
            discount=data.get('discount', 0.0),
            total_price=data['total_price'],
            payment_method=data.get('payment_method', 'Cash'),
            payment_id=data.get('payment_id'),
            status='Preparing'
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        # Emit real-time notification to admin dashboard
        order_dict = new_order.to_dict()
        socketio.emit('new_order', order_dict, room='admin')
        
        return jsonify(order_dict), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """
    Update order status
    """
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        if new_status not in ['Preparing', 'Ready', 'Completed', 'Cancelled']:
            return jsonify({'error': 'Invalid status'}), 400
        
        order = Order.query.get_or_404(order_id)
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Emit real-time notification to all connected clients
        order_dict = order.to_dict()
        socketio.emit('order_status_update', order_dict)
        
        return jsonify(order_dict)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """
    Get a specific order by ID
    """
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify(order.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    Delete an order (admin only)
    """
    try:
        order = Order.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        
        # Emit real-time notification
        socketio.emit('order_deleted', {'id': order_id})
        
        return jsonify({'message': 'Order deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get dashboard statistics
    """
    try:
        today = date.today()
        
        # Today's orders
        today_orders = Order.query.filter(func.date(Order.created_at) == today).all()
        
        # Status counts
        preparing_count = Order.query.filter(Order.status == 'Preparing').count()
        ready_count = Order.query.filter(Order.status == 'Ready').count()
        
        # Today's revenue
        today_revenue = sum(order.total_price for order in today_orders)
        
        # This week's revenue
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())
        week_orders = Order.query.filter(func.date(Order.created_at) >= week_start).all()
        week_revenue = sum(order.total_price for order in week_orders)
        
        stats = {
            'preparing_orders': preparing_count,
            'ready_orders': ready_count,
            'today_orders_count': len(today_orders),
            'today_revenue': today_revenue,
            'week_revenue': week_revenue,
            'total_orders': Order.query.count()
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/menu/items', methods=['POST'])
def add_menu_item():
    """
    Add a new menu item (admin only)
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['item_name', 'price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        new_item = MenuItem(
            item_name=data['item_name'],
            description=data.get('description', ''),
            price=data['price'],
            category=data.get('category', 'Main Course'),
            veg_nonveg=data.get('veg_nonveg', 'Veg'),
            is_available=data.get('is_available', True)
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return jsonify(new_item.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/menu/items/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    """
    Update a menu item (admin only)
    """
    try:
        data = request.get_json()
        item = MenuItem.query.get_or_404(item_id)
        
        # Update fields
        if 'item_name' in data:
            item.item_name = data['item_name']
        if 'description' in data:
            item.description = data['description']
        if 'price' in data:
            item.price = data['price']
        if 'category' in data:
            item.category = data['category']
        if 'veg_nonveg' in data:
            item.veg_nonveg = data['veg_nonveg']
        if 'is_available' in data:
            item.is_available = data['is_available']
        
        db.session.commit()
        
        return jsonify(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- WebSocket Events ---

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_admin')
def handle_join_admin():
    """Allow admin clients to join the admin room for notifications"""
    from flask_socketio import join_room
    join_room('admin')
    print(f'Admin client joined: {request.sid}')

@socketio.on('leave_admin')
def handle_leave_admin():
    """Allow admin clients to leave the admin room"""
    from flask_socketio import leave_room
    leave_room('admin')
    print(f'Admin client left: {request.sid}')

# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
