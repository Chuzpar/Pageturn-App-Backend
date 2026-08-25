import os
from datetime import timedelta
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

# --- Shared extension instances ---
# Model files (owned by M1/M2/M3) import `db` from this module.
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app():
    """Application factory: builds and configures the Flask app."""
    app = Flask(__name__)

    # --- Database config (PostgreSQL) ---
    database_url = os.environ.get("DATABASE_URL", "sqlite:///pageturn.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- JWT config (auth.py uses flask_jwt_extended) ---
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

    # --- Init extensions with this app instance ---
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)  # allows the Expo frontend to call this API during dev

    # --- Register blueprints ---
    # auth_bp is live (Sprint 1). The rest are stubs until their owners build them out.
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # from app.routes.books import books_bp
    # app.register_blueprint(books_bp, url_prefix="/api/books")

    # from app.routes.cart import cart_bp
    # app.register_blueprint(cart_bp, url_prefix="/api/cart")

    # from app.routes.orders import orders_bp
    # app.register_blueprint(orders_bp, url_prefix="/api/orders")

    # from app.routes.lending import lending_bp
    # app.register_blueprint(lending_bp, url_prefix="/api/lending")

    # from app.routes.admin import admin_bp
    # app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.route("/api/health")
    def health():
        """Quick sanity check that the server is up."""
        return jsonify({"status": "ok", "service": "PageTurn API"})

    return app
