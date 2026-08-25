from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password")

    if not full_name or not email or not password:
        return jsonify({"error": "full_name, email, and password are required"}), 400
    if confirm_password is not None and confirm_password != password:
        return jsonify({"error": "Passwords do not match"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(full_name=full_name, email=email, role=data.get("role", "member"))
    user.set_password(password)  # Task 10: password hashing
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(force=True, silent=True) or {}
    full_name = data.get("full_name")
    email = data.get("email")
    new_password = data.get("new_password")
    current_password = data.get("current_password")

    if full_name:
        user.full_name = full_name.strip()

    if email and email.strip().lower() != user.email:
        new_email = email.strip().lower()
        if User.query.filter(User.email == new_email, User.id != user.id).first():
            return jsonify({"error": "That email is already in use"}), 409
        user.email = new_email

    if new_password:
        # Changing the password requires re-confirming the current one.
        if not current_password or not user.check_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        if len(new_password) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400
        user.set_password(new_password)

    db.session.commit()
    return jsonify({"user": user.to_dict()})
