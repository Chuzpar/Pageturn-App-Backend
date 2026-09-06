from datetime import datetime
from app import db


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    cart_type = db.Column(db.String(20), nullable=False, default="purchase")  # 'purchase' | 'lending'
    lending_days = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    book = db.relationship("Book")

    def to_dict(self):
        return {
            "id": self.id,
            "book": self.book.to_dict() if self.book else None,
            "quantity": self.quantity,
            "cart_type": self.cart_type,
            "lending_days": self.lending_days,
        }