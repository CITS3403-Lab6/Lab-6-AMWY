import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name="development"):
    """Application factory"""
    package_dir = os.path.abspath(os.path.dirname(__file__))
    static_dir = os.path.abspath(os.path.join(package_dir, "..", "static"))

    app = Flask(__name__, static_folder=static_dir, static_url_path="/static")
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    login_manager.login_message = "Please log in to access this page."
    
    # Create instance folder
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Database schema initialization should be handled explicitly
    # via a dedicated setup or migration step, not on app startup.
    
    return app