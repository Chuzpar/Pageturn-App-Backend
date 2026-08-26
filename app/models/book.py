from datetime import datetime

from app import db


class Book(db.Model):
	__tablename__ = "books"

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	author = db.Column(db.String(120), nullable=False)
	description = db.Column(db.Text)
	cover_url = db.Column(db.String(500))
	price = db.Column(db.Float, nullable=False, default=0.0)
	genre = db.Column(db.String(80))
	rating = db.Column(db.Float, nullable=False, default=0.0)
	stock_for_lending = db.Column(db.Integer, nullable=False, default=0)
	is_new_arrival = db.Column(db.Boolean, nullable=False, default=False)
	is_popular = db.Column(db.Boolean, nullable=False, default=False)
	submitted_by_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))
	created_at = db.Column(db.DateTime, default=datetime.utcnow)

	def to_dict(self):
		return {
			"id": self.id,
			"title": self.title,
			"author": self.author,
			"description": self.description,
			"cover_url": self.cover_url,
			"price": self.price,
			"genre": self.genre,
			"rating": self.rating,
			"stock_for_lending": self.stock_for_lending,
			"is_new_arrival": self.is_new_arrival,
			"is_popular": self.is_popular,
			"created_at": self.created_at.isoformat() if self.created_at else None,
		}
