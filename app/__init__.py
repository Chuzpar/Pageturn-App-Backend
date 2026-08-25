import os
from datetime import timedelta
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_overrides=None):
    app = Flask(__name__)

    # --- Sprint 1, Task 2 & 3: Configure Flask Backend / PostgreSQL Database ---
    database_url = os.environ.get("DATABASE_URL", "sqlite:///pageturn.db")
    # Render/Heroku style URLs sometimes use postgres:// — SQLAlchemy needs postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # --- Register blueprints (one per feature area, matching the sprints) ---
    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.cart import cart_bp
    from app.routes.orders import orders_bp
    from app.routes.lending import lending_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(books_bp, url_prefix="/api/books")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(lending_bp, url_prefix="/api/lending")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "PageTurn API"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        from app.models import user, book, cart, order, lending  # noqa: F401
        db.create_all()

    return app
