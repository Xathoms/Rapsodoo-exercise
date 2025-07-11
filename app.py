import logging
import os
from datetime import date, datetime

from flask import Flask, render_template

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

    register_error_handlers(app)

    with app.app_context():
        create_database_tables()

    logger.info(f"COVID-19 Italy application created with config: {config_name}")
    return app


def register_error_handlers(app):
    """Register application-level error handlers."""

    @app.errorhandler(404)
    def handle_404(error):
        """Handle 404 Not Found errors."""
        logger.warning(
            f"404 error: {error} - URL: {error.description if hasattr(error, 'description') else 'Unknown'}"
        )
        return render_template(
            "error.html",
            error_message="The page you're looking for doesn't exist.",
            error_code="404",
        ), 404

    @app.errorhandler(500)
    def handle_500(error):
        """Handle 500 Internal Server errors."""
        logger.error(f"500 error: {error}")
        return render_template(
            "error.html",
            error_message="An internal server error occurred. Please try again later.",
            error_code="500",
        ), 500

    @app.errorhandler(503)
    def handle_503(error):
        """Handle 503 Service Unavailable errors."""
        logger.error(f"503 error: {error}")
        return render_template(
            "error.html",
            error_message="The service is temporarily unavailable. Please try again in a few moments.",
            error_code="503",
        ), 503

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions."""
        logger.error(f"Unhandled exception: {error}", exc_info=True)

        # In development, show the actual error
        if app.config.get("DEBUG"):
            raise error

        return render_template(
            "error.html",
            error_message="An unexpected error occurred. Please try again later.",
            error_code="500",
        ), 500


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
