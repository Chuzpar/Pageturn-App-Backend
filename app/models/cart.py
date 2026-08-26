from app import db


class CartItem(db.Model):
	__tablename__ = "cart_items"

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
	book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
	quantity = db.Column(db.Integer, nullable=False, default=1)
	cart_type = db.Column(db.String(20), nullable=False, default="purchase")
	lending_days = db.Column(db.Integer)
	book = db.relationship("Book")

	def to_dict(self):
		return {
			"id": self.id,
			"book_id": self.book_id,
			"quantity": self.quantity,
			"cart_type": self.cart_type,
			"lending_days": self.lending_days,
			"book": self.book.to_dict() if self.book else None,
		}
