"""
Flask Admin Dashboard

Internal admin panel for managing migrations, users, and API keys.
"""

from flask import Flask
from flask_login import LoginManager
from app.database import db_session
from app.models import User


def create_app():
    """Flask application factory"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SESSION_TYPE'] = 'filesystem'

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db_session.query(User).get(int(user_id))

    # Register blueprints
    from .routes import auth, dashboard, migrations, users, api_keys

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(migrations.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(api_keys.bp)

    # Teardown database session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app
