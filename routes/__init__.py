from .main import main_bp
from .api import api_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")


__all__ = ["main_bp", "api_bp", "register_blueprints"]
