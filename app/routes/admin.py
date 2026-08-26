from flask import Blueprint, jsonify, request

from app import db
from app.models.book import Book
from app.models.lending import LendingRequest
from app.models.order import Order
from app.utils import admin_required, current_user


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    return jsonify({
        "total_books": Book.query.count(),
        "pending_lending_requests": LendingRequest.query.filter_by(status="pending").count(),
        "active_loans": LendingRequest.query.filter_by(status="approved").count(),
        "total_orders": Order.query.count(),
        "orders_awaiting_approval": Order.query.filter_by(status="paid").count(),
        "total_revenue": db.session.query(db.func.coalesce(db.func.sum(Order.total), 0.0)).scalar(),
    })


@admin_bp.route("/books", methods=["GET"])
@admin_required
def admin_list_books():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return jsonify({"books": [book.to_dict() for book in books]})


@admin_bp.route("/books", methods=["POST"])
@admin_required
def admin_create_book():
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    if not title or not author:
        return jsonify({"error": "title and author are required"}), 400
    book = Book(
        title=title,
        author=author,
        description=data.get("description"),
        cover_url=data.get("cover_url"),
        price=data.get("price", 0.0),
        genre=data.get("genre"),
        rating=data.get("rating", 0.0),
        stock_for_lending=data.get("stock_for_lending", 0),
        is_new_arrival=data.get("is_new_arrival", False),
        is_popular=data.get("is_popular", False),
        submitted_by_admin_id=current_user().id,
    )
    db.session.add(book)
    db.session.commit()
    return jsonify({"book": book.to_dict()}), 201


@admin_bp.route("/books/<int:book_id>", methods=["PUT"])
@admin_required
def admin_update_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    data = request.get_json(force=True, silent=True) or {}
    for field in ["title", "author", "description", "cover_url", "price", "genre",
                  "rating", "stock_for_lending", "is_new_arrival", "is_popular"]:
        if field in data:
            setattr(book, field, data[field])
    db.session.commit()
    return jsonify({"book": book.to_dict()})


@admin_bp.route("/books/<int:book_id>", methods=["DELETE"])
@admin_required
def admin_delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted"})


@admin_bp.route("/lending-requests", methods=["GET"])
@admin_required
def admin_list_lending_requests():
    status = request.args.get("status", "pending")
    query = LendingRequest.query
    if status != "all":
        query = query.filter_by(status=status)
    lending_requests = query.order_by(LendingRequest.requested_at.desc()).all()
    return jsonify({"requests": [item.to_dict() for item in lending_requests]})


@admin_bp.route("/lending-requests/<int:request_id>/approve", methods=["POST"])
@admin_required
def admin_approve_lending(request_id):
    lending_request = LendingRequest.query.get(request_id)
    if not lending_request:
        return jsonify({"error": "Request not found"}), 404
    if lending_request.status != "pending":
        return jsonify({"error": f"Request already {lending_request.status}"}), 400
    if lending_request.book.stock_for_lending <= 0:
        return jsonify({"error": "No copies available to lend"}), 400
    lending_request.approve()
    lending_request.book.stock_for_lending -= 1
    db.session.commit()
    return jsonify({"request": lending_request.to_dict()})


@admin_bp.route("/lending-requests/<int:request_id>/reject", methods=["POST"])
@admin_required
def admin_reject_lending(request_id):
    lending_request = LendingRequest.query.get(request_id)
    if not lending_request:
        return jsonify({"error": "Request not found"}), 404
    if lending_request.status != "pending":
        return jsonify({"error": f"Request already {lending_request.status}"}), 400
    data = request.get_json(force=True, silent=True) or {}
    lending_request.status = "rejected"
    lending_request.reviewer_notes = data.get("notes")
    db.session.commit()
    return jsonify({"request": lending_request.to_dict()})


@admin_bp.route("/orders", methods=["GET"])
@admin_required
def admin_list_orders():
    status = request.args.get("status")
    query = Order.query.order_by(Order.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    return jsonify({"orders": [order.to_dict() for order in query.all()]})


def _update_order_status(order_id, status):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    order.status = status
    db.session.commit()
    return jsonify({"order": order.to_dict()})


@admin_bp.route("/orders/<int:order_id>/approve", methods=["POST"])
@admin_required
def admin_approve_order(order_id):
    return _update_order_status(order_id, "approved")


@admin_bp.route("/orders/<int:order_id>/reject", methods=["POST"])
@admin_required
def admin_reject_order(order_id):
    return _update_order_status(order_id, "cancelled")


@admin_bp.route("/orders/<int:order_id>/advance", methods=["POST"])
@admin_required
def admin_advance_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    next_status = {"approved": "shipped", "shipped": "delivered"}.get(order.status)
    if not next_status:
        return jsonify({"error": f"Cannot advance order from {order.status}"}), 400
    order.status = next_status
    db.session.commit()
    return jsonify({"order": order.to_dict()})
