import logging
import os
from datetime import date, datetime

from flask import Flask

from config import config
from database import db
from routes import register_blueprints


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app instances.

    Args:
        config_name: Configuration to use (development, production, testing)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config[config_name])

    db.init_app(app)
    register_blueprints(app)

    @app.template_global()
    def now():
        """Make current datetime available in templates."""
        return datetime.now()

    @app.template_global()
    def today():
        """Make current date available in templates."""
        return date.today()

    with app.app_context():
        create_database_tables()

    logger.info(f"COVID-19 Italy application created with config: {config_name}")
    return app


def create_database_tables():
    """Create database tables if they don't exist."""
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


app = create_app()


if __name__ == "__main__":
    port = app.config.get("PORT", 5000)
    debug = app.config.get("DEBUG", False)

    logger.info(f"Starting COVID-19 Italy application on port {port}")

    app.run(host="0.0.0.0", port=port, debug=debug)
