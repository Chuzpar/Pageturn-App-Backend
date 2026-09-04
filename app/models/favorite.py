from datetime import datetime
from app import db


class Favorite(db.Model):
    __tablename__ = "favorites"
    __table_args__ = (db.UniqueConstraint("user_id", "book_id", name="one_favorite_per_user_per_book"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    book = db.relationship("Book")

    def to_dict(self):
        return {
            "id": self.id,
            "book": self.book.to_dict() if self.book else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
