import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from app.config import config
from flask_wtf import CSRFProtect


db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(config_name="development"):
    """Create and configure the HabitWise Flask application."""

    package_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(package_dir, ".."))
    static_dir = os.path.join(project_root, "static")

    app = Flask(
        __name__,
        static_folder=static_dir,
        static_url_path="/static",
    )

    app.config.from_object(config[config_name])

    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    os.makedirs(app.instance_path, exist_ok=True)

    from app.routes import main
    app.register_blueprint(main)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()


    _apply_security_config(app)
    _register_security_headers(app)

    return app

# ---------------------------------------------------------------------------
# Security hardening
# ---------------------------------------------------------------------------

def _apply_security_config(app):
    """Apply safe session/cookie security defaults.

    These settings do not change user flows, but they make browser-side session
    handling safer by default.
    """
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"


def _register_security_headers(app):
    """Register basic browser security headers for every response."""
    if getattr(app, "_habitwise_security_headers_registered", False):
        return

    app._habitwise_security_headers_registered = True

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )

        # Prevent sensitive HTML pages being stored in browser/shared caches.
        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("text/html"):
            response.headers.setdefault("Cache-Control", "no-store")
            response.headers.setdefault("Pragma", "no-cache")

        return response

