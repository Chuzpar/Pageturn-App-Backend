from flask import Blueprint, request, jsonify
from app import db
from app.models.book import Book
from app.models.lending import LendingRequest
from app.models.order import Order
from app.utils import admin_required, current_user

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/books", methods=["GET"])
@admin_required
def admin_list_books():

# ===== BOOK MANAGEMENT (Sprint 2 - Member 4) =====

@admin_bp.route("/books", methods=["GET"])
@admin_required
def admin_list_books():
    """
    Retrieve all books for admin management.
    Returns books ordered by creation date (newest first).
    """
    books = Book.query.order_by(Book.created_at.desc()).all()
    return jsonify({"books": [b.to_dict() for b in books]})


@admin_bp.route("/books", methods=["POST"])
@admin_required
def admin_create_book():
    """Add New Manuscript screen -> creates a Book."""
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    """
    Create a new book in the catalogue.
    Used by Add New Manuscript screen.
    
    Required fields:
        - title: Book title
        - author: Book author
    
    Optional fields:
        - description: Book description
        - cover_url: Cover image URL
        - price: Retail price
        - genre: Book genre
        - rating: Book rating
        - stock_for_lending: Number of copies available
        - is_new_arrival: Boolean flag
        - is_popular: Boolean flag
    """
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
    
    db.session.add(book)
    db.session.commit()
    
    return jsonify({"book": book.to_dict()}), 201


@admin_bp.route("/books/<int:book_id>", methods=["PUT"])
@admin_required
def admin_update_book(book_id):
    """Sprint 2 - Task 13: Implement Update Book"""
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    data = request.get_json(force=True, silent=True) or {}
    for field in ["title", "author", "description", "cover_url", "price", "genre",
                  "rating", "stock_for_lending", "is_new_arrival", "is_popular"]:
        if field in data:
            setattr(book, field, data[field])
    """
    Update an existing book.
    Used by Edit Manuscript screen.
    """
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    
    data = request.get_json(force=True, silent=True) or {}
    
    # Update only fields that are provided
    updatable_fields = [
        "title", "author", "description", "cover_url", 
        "price", "genre", "rating", "stock_for_lending",
        "is_new_arrival", "is_popular"
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(book, field, data[field])
    
    db.session.commit()
    return jsonify({"book": book.to_dict()})


@admin_bp.route("/books/<int:book_id>", methods=["DELETE"])
@admin_required
def admin_delete_book(book_id):
    """Sprint 2 - Task 14: Implement Delete Book"""
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
    reqs = query.order_by(LendingRequest.requested_at.desc()).all()
    return jsonify({"requests": [r.to_dict() for r in reqs]})
    """
    Delete a book from the catalogue.
    Used by Admin Books screen.
    """
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({"message": "Book deleted successfully"})


# ===== LENDING MANAGEMENT (Sprint 4 - Member 4) =====

@admin_bp.route("/lending-requests", methods=["GET"])
@admin_required
def admin_list_lending_requests():
    """
    Retrieve lending requests for admin management.
    Filter by status (pending, approved, rejected, all).
    """
    status = request.args.get("status", "pending")
    query = LendingRequest.query
    
    if status != "all":
        query = query.filter_by(status=status)
    
    requests = query.order_by(LendingRequest.requested_at.desc()).all()
    return jsonify({"requests": [r.to_dict() for r in requests]})


@admin_bp.route("/lending-requests/<int:request_id>/approve", methods=["POST"])
@admin_required
def admin_approve_lending(request_id):
    """Sprint 4 - Task 10: Implement Approve Lending Request"""
    lr = LendingRequest.query.get(request_id)
    if not lr:
        return jsonify({"error": "Request not found"}), 404
    if lr.status != "pending":
        return jsonify({"error": f"Request already {lr.status}"}), 400
    if lr.book.stock_for_lending <= 0:
        return jsonify({"error": "No copies available to lend"}), 400

    lr.approve()
    lr.book.stock_for_lending -= 1
    db.session.commit()
    return jsonify({"request": lr.to_dict()})
    """
    Approve a lending request.
    Decreases book stock and sets due date.
    """
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
    """Sprint 4 - Task 11: Implement Reject Lending Request"""
    lr = LendingRequest.query.get(request_id)
    if not lr:
        return jsonify({"error": "Request not found"}), 404
    if lr.status != "pending":
        return jsonify({"error": f"Request already {lr.status}"}), 400

    data = request.get_json(force=True, silent=True) or {}
    lr.status = "rejected"
    lr.reviewer_notes = data.get("notes")
    db.session.commit()
    return jsonify({"request": lr.to_dict()})

    """
    Reject a lending request with optional notes.
    """
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


# ===== ORDER MANAGEMENT (Sprint 5 - Member 4) =====

@admin_bp.route("/orders", methods=["GET"])
@admin_required
def admin_list_orders():
    status = request.args.get("status")
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    """
    Retrieve all purchase orders for admin management.
    Filter by status if provided.
    """
    status = request.args.get("status")
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify({"orders": [o.to_dict() for o in orders]})


# Order status flow
ORDER_STATUS_FLOW = ["paid", "approved", "shipped", "delivered"]


@admin_bp.route("/orders/<int:order_id>/approve", methods=["POST"])
@admin_required
def admin_approve_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if order.status not in ("paid",):
        return jsonify({"error": f"Order cannot be approved from status '{order.status}'"}), 400
    order.status = "approved"
    db.session.commit()
    """
    Approve a paid order.
    Moves status from 'paid' to 'approved'.
    """
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    if order.status not in ("paid",):
        return jsonify({"error": f"Order cannot be approved from status '{order.status}'"}), 400
    
    order.status = "approved"
    db.session.commit()
    
    return jsonify({"order": order.to_dict()})


@admin_bp.route("/orders/<int:order_id>/reject", methods=["POST"])
@admin_required
def admin_reject_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if order.status not in ("paid", "approved"):
        return jsonify({"error": f"Order cannot be rejected from status '{order.status}'"}), 400
    order.status = "cancelled"
    db.session.commit()
    """
    Reject a paid or approved order.
    Moves status to 'cancelled'.
    """
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    if order.status not in ("paid", "approved"):
        return jsonify({"error": f"Order cannot be rejected from status '{order.status}'"}), 400
    
    order.status = "cancelled"
    db.session.commit()
    
    return jsonify({"order": order.to_dict()})


@admin_bp.route("/orders/<int:order_id>/advance", methods=["POST"])
@admin_required
def admin_advance_order(order_id):
    """Moves an approved order to the next fulfillment stage (shipped -> delivered)."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if order.status not in ("approved", "shipped"):
        return jsonify({"error": f"Order cannot be advanced from status '{order.status}'"}), 400
    next_index = ORDER_STATUS_FLOW.index(order.status) + 1
    order.status = ORDER_STATUS_FLOW[next_index]
    db.session.commit()
    return jsonify({"order": order.to_dict()})


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    """Sprint 5 - Task 7: Create Admin Dashboard API.
    Admin Panel welcome screen: totals shown at top (books, active loans, orders, revenue)."""
    """
    Advance an order to the next fulfillment stage.
    Moves status: approved -> shipped -> delivered.
    """
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    if order.status not in ("approved", "shipped"):
        return jsonify({"error": f"Order cannot be advanced from status '{order.status}'"}), 400
    
    next_index = ORDER_STATUS_FLOW.index(order.status) + 1
    order.status = ORDER_STATUS_FLOW[next_index]
    db.session.commit()
    
    return jsonify({"order": order.to_dict()})


# ===== ADMIN DASHBOARD (Sprint 5 - Member 4) =====

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    """
    Get dashboard statistics for admin panel.
    Returns counts for books, lending requests, orders, and revenue.
    """
    # Calculate total revenue from completed orders
    revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.status.in_(["paid", "approved", "shipped", "delivered"])
    ).scalar() or 0.0

    return jsonify({
        "total_books": Book.query.count(),
        "pending_lending_requests": LendingRequest.query.filter_by(status="pending").count(),
        "active_loans": LendingRequest.query.filter_by(status="approved").count(),
        "total_orders": Order.query.count(),
        "orders_awaiting_approval": Order.query.filter_by(status="paid").count(),
        "total_revenue": round(revenue, 2),
    })
