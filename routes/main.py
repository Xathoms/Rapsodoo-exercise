import logging
from datetime import datetime

from flask import Blueprint, current_app, render_template, request
from sqlalchemy import func

from database import db
from models.covid_data import CovidDataRecord
from services import CovidDataService, RegionalDataService
from utils import parse_date_input

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)
regional_service = RegionalDataService()


def get_covid_service():
    """
    Get COVID service instance with proper timeout from application config.

    Returns:
        CovidDataService: Configured service instance with request timeout
    """
    timeout = current_app.config.get("REQUEST_TIMEOUT", 30)
    return CovidDataService(timeout=timeout)


@main_bp.route("/")
def index():
    """
    Main page displaying regional COVID-19 statistics with intelligent caching.

    This endpoint serves the primary dashboard showing regional COVID-19 case data.
    It implements smart caching strategies to minimize API calls while ensuring
    data freshness, and provides comprehensive error handling with user feedback.

    Returns:
        flask.Response: Rendered HTML template with regional statistics or error page
    """
    try:
        covid_service = get_covid_service()
        search_date = request.args.get("date", "latest")

        parsed_date = "latest"
        if search_date and search_date != "latest":
            parsed_date = parse_date_input(search_date)
            if parsed_date is None:
                parsed_date = "latest"

        regional_summaries, status_message = (
            regional_service.get_regional_summary_smart(
                target_date=parsed_date, covid_service=covid_service
            )
        )

        logger.info(f"Data retrieval status: {status_message}")

        if not regional_summaries:
            available_dates = _get_available_dates_sample()
            return render_template(
                "index.html",
                regional_summaries=[],
                total_cases=0,
                total_regions=0,
                current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                search_date=search_date,
                available_dates=available_dates,
                historical_start=current_app.config["HISTORICAL_START_DATE"].strftime(
                    "%Y-%m-%d"
                ),
                status_message=status_message,
            )

        total_cases = sum(summary.total_cases for summary in regional_summaries)
        total_regions = len(regional_summaries)

        available_dates = _get_available_dates_sample()

        return render_template(
            "index.html",
            regional_summaries=regional_summaries,
            total_cases=total_cases,
            total_regions=total_regions,
            current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            search_date=search_date,
            available_dates=available_dates,
            historical_start=current_app.config["HISTORICAL_START_DATE"].strftime(
                "%Y-%m-%d"
            ),
            status_message=status_message,
        )

    except Exception as e:
        logger.error(f"Application error in main route: {e}")
        return render_template(
            "error.html",
            error_message="An internal error occurred. Please try again later.",
        ), 500


def _get_available_dates_sample(limit: int = 30) -> list:
    """
    Get a sample of available dates from the database for UI guidance.

    This helper function retrieves a limited set of available dates to show
    users what data is actually available, helping them make informed date selections.

    Args:
        limit (int): Maximum number of dates to return. Defaults to 30.

    Returns:
        list: List of date objects representing available data dates,
            sorted in descending order (most recent first)
    """
    try:
        dates = (
            db.session.query(func.distinct(func.date(CovidDataRecord.data_timestamp)))
            .order_by(func.date(CovidDataRecord.data_timestamp).desc())
            .limit(limit)
            .all()
        )
        return [d[0] for d in dates]
    except Exception as e:
        logger.error(f"Failed to get available dates sample: {e}")
        return []


@main_bp.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors with user-friendly error page."""
    return render_template("error.html", error_message="Page not found."), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors with logging and generic user message."""
    logger.error(f"Internal server error: {error}")
    return render_template("error.html", error_message="Internal server error."), 500
