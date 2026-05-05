import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from app.config import config


db = SQLAlchemy()
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

    return app
