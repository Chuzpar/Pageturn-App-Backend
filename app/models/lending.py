from datetime import datetime, timedelta
from app import db


class LendingRequest(db.Model):
    """Sprint 4 - Task 1: Create Lending Database Model
    Tracks the full lifecycle: pending -> approved/rejected -> borrowed -> returned."""
    __tablename__ = "lending_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    lending_days = db.Column(db.Integer, default=14)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected, returned
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    returned_at = db.Column(db.DateTime, nullable=True)
    reviewer_notes = db.Column(db.String(300), nullable=True)

    book = db.relationship("Book")

    def approve(self):
        self.status = "approved"
        self.approved_at = datetime.utcnow()
        self.due_date = datetime.utcnow() + timedelta(days=self.lending_days or 14)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book": self.book.to_dict() if self.book else None,
            "lending_days": self.lending_days,
            "status": self.status,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
        }