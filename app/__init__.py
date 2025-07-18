from flask import Flask
from app.config import get_config
from app.extensions import db, migrate, cors
from app.admin import init_admin
from app.controllers.users import users_bp
from app.controllers.guilds import guilds_bp
from app.error_handlers import register_error_handlers


def create_app(env: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(env))

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    if not app.config.get("TESTING"):
        init_admin(app)  # Only load Flask-Admin outside of tests

    # Register error handlers
    register_error_handlers(app)

    # register blueprints
    app.register_blueprint(users_bp, url_prefix="/api/v1")
    app.register_blueprint(guilds_bp, url_prefix="/api/v1")

    # health check
    @app.get("/ping")
    def ping():
        return {"status": "ok"}

    return app
