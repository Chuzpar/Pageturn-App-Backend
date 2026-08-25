import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate

# --- Shared extension instances ---
# These get initialized here but bound to the app inside create_app().
# Model files (owned by M1/M2/M3) will import `db` from this module.
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    """Application factory: builds and configures the Flask app."""
    app = Flask(__name__)

    # --- Database config (PostgreSQL) ---
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "postgresql://localhost:5432/bookapp_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Secret key (used later for auth/session tokens) ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # --- Init extensions with this app instance ---
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)  # allows the Expo frontend to call this API during dev

    # --- Blueprints get registered here as each route owner builds theirs ---
    # from app.routes.auth import auth_bp
    # app.register_blueprint(auth_bp, url_prefix="/api/auth")

    @app.route("/api/health")
    def health():
        """Quick sanity check that the server is up."""
        return {"status": "ok"}