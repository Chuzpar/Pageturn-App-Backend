from datetime import datetime
from uuid import uuid4
from app import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    shipping_address = db.Column(db.String(300), nullable=True)
    payment_method_last4 = db.Column(db.String(4), nullable=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    shipping_fee = db.Column(db.Float, nullable=False, default=4.99)
    tax = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(30), default="pending")
    merchant_reference = db.Column(db.String(80), unique=True, nullable=False,
                                   default=lambda: str(uuid4()))
    pesapal_tracking_id = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "shipping_address": self.shipping_address,
            "payment_method_last4": self.payment_method_last4,
            "subtotal": self.subtotal,
            "shipping_fee": self.shipping_fee,
            "tax": self.tax,
            "total": self.total,
            "status": self.status,
            "merchant_reference": self.merchant_reference,
            "pesapal_tracking_id": self.pesapal_tracking_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [i.to_dict() for i in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_at_purchase = db.Column(db.Float, nullable=False)

    book = db.relationship("Book")

    def to_dict(self):
        return {
            "id": self.id,
            "book": self.book.to_dict() if self.book else None,
            "quantity": self.quantity,
            "price_at_purchase": self.price_at_purchase,
        }
