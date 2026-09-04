from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.utils import current_user

orders_bp = Blueprint("orders", __name__)

TAX_RATE = 0.08

@orders_bp.route("/checkout", methods=["POST"])
@jwt_required()
def checkout():
    """Consolidates: Checkout Screen -> Payment Workflow -> Order creation."""
    user = current_user()
    data = request.get_json(force=True, silent=True) or {}

    cart_items = CartItem.query.filter_by(user_id=user.id, cart_type="purchase").all()
    if not cart_items:
        return jsonify({"error": "Your purchase cart is empty"}), 400

    shipping_address = data.get("shipping_address")
    card_number = data.get("card_number", "")
    if not shipping_address:
        return jsonify({"error": "Shipping address is required"}), 400
    if not card_number or len(card_number.replace(" ", "")) < 12:
        return jsonify({"error": "A valid card number is required"}), 400

    subtotal = sum(ci.book.price * ci.quantity for ci in cart_items if ci.book)
    shipping_fee = 4.99 if subtotal > 0 else 0.0
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + shipping_fee + tax, 2)

    order = Order(
        user_id=user.id,
        shipping_address=shipping_address,
        payment_method_last4=card_number.replace(" ", "")[-4:],
        subtotal=round(subtotal, 2),
        shipping_fee=shipping_fee,
        tax=tax,
        total=total,
        status="paid",
    )
    db.session.add(order)
    db.session.flush()  # get order.id

    for ci in cart_items:
        db.session.add(OrderItem(order_id=order.id, book_id=ci.book_id,
                                  quantity=ci.quantity, price_at_purchase=ci.book.price))
        db.session.delete(ci)  # empty the cart

    db.session.commit()
    return jsonify({"order": order.to_dict()}), 201

@orders_bp.route("", methods=["GET"])
@jwt_required()
def list_orders():
    user = current_user()
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return jsonify({"orders": [o.to_dict() for o in orders]})


@orders_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    user = current_user()
    order = Order.query.filter_by(id=order_id, user_id=user.id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"order": order.to_dict()})
