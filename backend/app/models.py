# backend/app/models.py

from . import db
from datetime import datetime

class MenuItem(db.Model):
    __tablename__ = 'menu_items'  # <-- ADD THIS LINE

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    veg_nonveg = db.Column(db.String(20))
    # Add any other columns from your table here if needed

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Order(db.Model):
    # ... (no changes needed for the Order model)
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False, default="Walk-in")
    items = db.Column(db.JSON, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Preparing')
    payment_method = db.Column(db.String(50), nullable=False, default='Cash')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

