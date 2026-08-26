from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.book import Book
from app.models.cart import CartItem
from app.utils import current_user

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("", methods=["GET"])
@jwt_required()
def get_cart():
    cart_type = request.args.get("type", "purchase")
    user = current_user()
    items = CartItem.query.filter_by(user_id=user.id, cart_type=cart_type).all()
    subtotal = sum((i.book.price * i.quantity) for i in items if i.cart_type == "purchase" and i.book)
    return jsonify({"items": [i.to_dict() for i in items], "subtotal": round(subtotal, 2)})


@cart_bp.route("/items", methods=["POST"])
@jwt_required()
def add_to_cart():
    data = request.get_json(force=True, silent=True) or {}
    book_id = data.get("book_id")
    cart_type = data.get("cart_type", "purchase")
    quantity = data.get("quantity", 1)
    lending_days = data.get("lending_days", 14 if cart_type == "lending" else None)

    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    user = current_user()
    existing = CartItem.query.filter_by(user_id=user.id, book_id=book_id, cart_type=cart_type).first()
    if existing and cart_type == "purchase":
        existing.quantity += quantity
        db.session.commit()
        return jsonify({"item": existing.to_dict()}), 200

    item = CartItem(user_id=user.id, book_id=book_id, quantity=quantity,
                     cart_type=cart_type, lending_days=lending_days)
    db.session.add(item)
    db.session.commit()
    return jsonify({"item": item.to_dict()}), 201


@cart_bp.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
def remove_from_cart(item_id):
    user = current_user()
    item = CartItem.query.filter_by(id=item_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "Cart item not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item removed"})


@cart_bp.route("/items/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update_cart_item(item_id):
    user = current_user()
    item = CartItem.query.filter_by(id=item_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "Cart item not found"}), 404
    data = request.get_json(force=True, silent=True) or {}
    if "quantity" in data:
        item.quantity = max(1, int(data["quantity"]))
    if "lending_days" in data:
        item.lending_days = data["lending_days"]
    db.session.commit()
    return jsonify({"item": item.to_dict()})
    return jsonify({"item": item.to_dict()})
