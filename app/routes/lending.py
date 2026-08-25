from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.cart import CartItem
from app.models.lending import LendingRequest
from app.utils import current_user

lending_bp = Blueprint("lending", __name__)

@lending_bp.route("/requests", methods=["POST"])
@jwt_required()
def submit_lending_requests():
    """Initiate Return / Lending Request screen submit -> turns every item
    in the user's lending cart into a LendingRequest and clears that cart."""
    user = current_user()
    cart_items = CartItem.query.filter_by(user_id=user.id, cart_type="lending").all()
    if not cart_items:
        return jsonify({"error": "Your lending cart is empty"}), 400

    created = []
    for ci in cart_items:
        lr = LendingRequest(user_id=user.id, book_id=ci.book_id,
                             lending_days=ci.lending_days or 14, status="pending")
        db.session.add(lr)
        db.session.flush()
        created.append(lr)
        db.session.delete(ci)

    db.session.commit()
    return jsonify({"requests": [r.to_dict() for r in created]}), 201


@lending_bp.route("/requests", methods=["GET"])
@jwt_required()
def my_lending_requests():
    user = current_user()
    status = request.args.get("status")  # optional filter
    query = LendingRequest.query.filter_by(user_id=user.id)
    if status:
        query = query.filter_by(status=status)
    reqs = query.order_by(LendingRequest.requested_at.desc()).all()
    return jsonify({"requests": [r.to_dict() for r in reqs]})


@lending_bp.route("/borrowed", methods=["GET"])
@jwt_required()
def my_borrowed_books():
    user = current_user()
    borrowed = LendingRequest.query.filter_by(user_id=user.id, status="approved").all()
    return jsonify({"borrowed": [r.to_dict() for r in borrowed]})

@lending_bp.route("/requests/<int:request_id>/return", methods=["POST"])
@jwt_required()
def initiate_return(request_id):
    user = current_user()
    lr = LendingRequest.query.filter_by(id=request_id, user_id=user.id).first()
    if not lr:
        return jsonify({"error": "Loan not found"}), 404
    if lr.status != "approved":
        return jsonify({"error": "This item isn't currently borrowed"}), 400

    lr.status = "returned"
    lr.returned_at = datetime.utcnow()
    lr.book.stock_for_lending += 1
    db.session.commit()
    return jsonify({"request": lr.to_dict()})
