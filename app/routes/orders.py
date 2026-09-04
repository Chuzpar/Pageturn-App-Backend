from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from app import db
from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.pesapal import PesapalClient, PesapalError
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
    if not shipping_address:
        return jsonify({"error": "Shipping address is required"}), 400

    subtotal = sum(ci.book.price * ci.quantity for ci in cart_items if ci.book)
    shipping_fee = 4.99 if subtotal > 0 else 0.0
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + shipping_fee + tax, 2)

    order = Order(
        user_id=user.id,
        shipping_address=shipping_address,
        subtotal=round(subtotal, 2),
        shipping_fee=shipping_fee,
        tax=tax,
        total=total,
        status="pending",
    )
    db.session.add(order)
    db.session.flush()  # get order.id

    for ci in cart_items:
        db.session.add(OrderItem(order_id=order.id, book_id=ci.book_id,
                                  quantity=ci.quantity, price_at_purchase=ci.book.price))
        db.session.delete(ci)  # empty the cart

    db.session.commit()

    callback_url = current_app.config.get("PESAPAL_CALLBACK_URL")
    if not callback_url:
        return jsonify({"error": "PESAPAL_CALLBACK_URL is not configured", "order": order.to_dict()}), 503

    billing_address = data.get("billing_address") or {"email_address": user.email}
    try:
        payment = PesapalClient().submit_order(order, callback_url, billing_address)
    except PesapalError as exc:
        return jsonify({"error": str(exc), "order": order.to_dict()}), 502

    order.pesapal_tracking_id = payment["order_tracking_id"]
    db.session.commit()
    return jsonify({"order": order.to_dict(), "redirect_url": payment["redirect_url"]}), 201


def _update_payment_status(tracking_id, merchant_reference):
    order = Order.query.filter(
        or_(Order.pesapal_tracking_id == tracking_id,
            Order.merchant_reference == merchant_reference)
    ).first()
    if not order:
        return None, (jsonify({"error": "Order not found"}), 404)

    try:
        payment = PesapalClient().transaction_status(tracking_id)
    except PesapalError as exc:
        return None, (jsonify({"error": str(exc)}), 502)

    status = (payment.get("payment_status_description") or "").upper()
    if status == "COMPLETED":
        order.status = "paid"
    elif status in ("FAILED", "INVALID"):
        order.status = "payment_failed"
    else:
        order.status = "pending"
    order.pesapal_tracking_id = tracking_id
    db.session.commit()
    return order, None


@orders_bp.route("/pesapal/callback", methods=["GET", "POST"])
def pesapal_callback():
    values = request.args if request.method == "GET" else (request.get_json(silent=True) or request.form)
    tracking_id = values.get("OrderTrackingId")
    merchant_reference = values.get("OrderMerchantReference")
    if not tracking_id or not merchant_reference:
        return jsonify({"error": "OrderTrackingId and OrderMerchantReference are required"}), 400
    order, error = _update_payment_status(tracking_id, merchant_reference)
    if error:
        return error
    return jsonify({"order": order.to_dict()})


@orders_bp.route("/pesapal/ipn", methods=["GET", "POST"])
def pesapal_ipn():
    values = request.args if request.method == "GET" else (request.get_json(silent=True) or request.form)
    tracking_id = values.get("OrderTrackingId")
    merchant_reference = values.get("OrderMerchantReference")
    if not tracking_id or not merchant_reference:
        return jsonify({"error": "OrderTrackingId and OrderMerchantReference are required"}), 400
    order, error = _update_payment_status(tracking_id, merchant_reference)
    if error:
        return error
    return jsonify({
        "orderNotificationType": "IPNCHANGE",
        "orderTrackingId": tracking_id,
        "orderMerchantReference": merchant_reference,
        "status": 200,
    })

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
