from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.utils import current_user
from app.mpesa import stk_push

mpesa_bp = Blueprint("mpesa", __name__)

TAX_RATE = 0.08


@mpesa_bp.route("/stkpush", methods=["POST"])
@jwt_required()
def initiate_stk_push():
    """
    Starts the M-Pesa checkout flow:
    1. Reads the user's purchase cart (same as card checkout).
    2. Creates an Order in 'pending' status (not yet paid).
    3. Triggers a real STK Push prompt to the given phone number.
    The order is marked 'paid' later by the /callback route once
    Safaricom confirms the payment.
    """
    user = current_user()
    data = request.get_json(force=True, silent=True) or {}

    phone = data.get("phone", "").strip()
    shipping_address = data.get("shipping_address", "").strip()

    if not shipping_address:
        return jsonify({"error": "Shipping address is required"}), 400
    if not phone:
        return jsonify({"error": "M-Pesa phone number is required"}), 400

    cart_items = CartItem.query.filter_by(user_id=user.id, cart_type="purchase").all()
    if not cart_items:
        return jsonify({"error": "Your purchase cart is empty"}), 400

    subtotal = sum(ci.book.price * ci.quantity for ci in cart_items if ci.book)
    shipping_fee = 4.99 if subtotal > 0 else 0.0
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + shipping_fee + tax, 2)

    order = Order(
        user_id=user.id,
        shipping_address=shipping_address,
        payment_method_last4="mpesa",
        subtotal=round(subtotal, 2),
        shipping_fee=shipping_fee,
        tax=tax,
        total=total,
        status="pending",
    )
    db.session.add(order)
    db.session.flush()

    for ci in cart_items:
        db.session.add(OrderItem(order_id=order.id, book_id=ci.book_id,
                                  quantity=ci.quantity, price_at_purchase=ci.book.price))
    db.session.commit()

    try:
        result = stk_push(
            phone=phone,
            amount=total,
            account_reference=f"Order{order.id}",
            transaction_desc="PageTurn",
        )
    except Exception as e:
        order.status = "failed"
        db.session.commit()
        return jsonify({"error": f"Could not reach M-Pesa: {e}"}), 502

    if result.get("ResponseCode") != "0":
        order.status = "failed"
        db.session.commit()
        return jsonify({"error": result.get("ResponseDescription", "STK Push failed")}), 400

    order.mpesa_checkout_request_id = result.get("CheckoutRequestID")
    db.session.commit()

    return jsonify({
        "order": order.to_dict(),
        "message": "Check your phone to enter your M-Pesa PIN.",
    }), 200


@mpesa_bp.route("/callback", methods=["POST"])
def mpesa_callback():
    """
    Safaricom calls this URL after the customer completes (or cancels)
    the STK Push prompt. No auth here — Daraja calls it directly,
    identified instead by the CheckoutRequestID it sends back.
    """
    payload = request.get_json(force=True, silent=True) or {}
    stk_callback = payload.get("Body", {}).get("stkCallback", {})

    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")

    order = Order.query.filter_by(mpesa_checkout_request_id=checkout_request_id).first()
    if not order:
        return jsonify({"ResultCode": 0, "ResultDesc": "Order not found, ignored"}), 200

    if result_code == 0:
        order.status = "paid"
        CartItem.query.filter_by(user_id=order.user_id, cart_type="purchase").delete()
    else:
        order.status = "failed"

    db.session.commit()
    return jsonify({"ResultCode": 0, "ResultDesc": "Callback processed"}), 200
