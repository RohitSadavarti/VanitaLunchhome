from flask import request, jsonify, Blueprint
from . import db, socketio
from .models import MenuItem, Order

bp = Blueprint('api', __name__)

# --- API Routes ---

@bp.route('/api/menu', methods=['GET'])
def get_menu():
    """
    This function executes a query equivalent to:
    SELECT id, item_name, description, price, category, veg_nonveg 
    FROM menu_items;
    """
    menu_items = MenuItem.query.all() # This is the correct query
    return jsonify([item.to_dict() for item in menu_items])

@bp.route('/api/orders', methods=['GET'])
def get_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])

@bp.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = Order(
        items=data['items'],
        total_price=data['total_price'],
        payment_method=data.get('payment_method', 'Cash')
    )
    db.session.add(new_order)
    db.session.commit()
    
    # Notify admin dashboard via WebSocket
    socketio.emit('new_order', new_order.to_dict())
    
    return jsonify(new_order.to_dict()), 201

@bp.route('/api/orders/<int:id>/status', methods=['PUT'])
def update_order_status(id):
    data = request.get_json()
    order = Order.query.get_or_404(id)
    order.status = data['status']
    db.session.commit()
    
    # Notify all clients (customer and admin) about the status change
    socketio.emit('order_status_update', order.to_dict())
    
    return jsonify(order.to_dict())

# --- WebSocket Events ---

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
