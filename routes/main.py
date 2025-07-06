import logging
from datetime import datetime

from flask import Blueprint, current_app, flash, render_template, request

from services import CovidDataService, RegionalDataService
from utils import parse_date_input

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)


def get_covid_service():
    """Get COVID service with proper timeout from config."""
    timeout = current_app.config.get("REQUEST_TIMEOUT", 30)
    return CovidDataService(timeout=timeout)


covid_service = None
regional_service = RegionalDataService()


def get_services():
    """Initialize services if needed."""
    global covid_service
    if covid_service is None:
        covid_service = get_covid_service()
    return covid_service, regional_service


@main_bp.route("/")
def index():
    """Main page displaying regional COVID-19 statistics."""
    try:
        covid_service, regional_service = get_services()

        search_date = request.args.get("date", "latest")
        sort_by = request.args.get("sort", "cases_desc")

        parsed_date = "latest"
        if search_date and search_date != "latest":
            parsed_date = parse_date_input(search_date)
            if parsed_date is None:
                flash(
                    f"Invalid date format: {search_date}. Please use YYYY-MM-DD format.",
                    "error",
                )
                parsed_date = "latest"

        if regional_service.should_refresh_data(
            current_app.config["DATA_CACHE_MINUTES"]
        ):
            try:
                logger.info("Refreshing COVID-19 data...")
                province_data = covid_service.fetch_all_historical_data()
                covid_service.save_to_database(province_data, "full")
            except Exception as e:
                logger.error(f"Failed to refresh data: {e}")

                try:
                    logger.info("Attempting to fetch latest data as fallback...")
                    latest_data = covid_service.fetch_latest_data()
                    covid_service.save_to_database(latest_data, "latest")
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
                    flash(
                        "Unable to fetch latest data. Showing cached data.", "warning"
                    )

        regional_summaries = regional_service.get_regional_summary_for_date(
            target_date=parsed_date, sort_by=sort_by
        )

        if not regional_summaries:
            try:
                logger.info("No data found, attempting initial fetch")
                province_data = covid_service.fetch_all_historical_data()
                covid_service.save_to_database(province_data, "full")
                regional_summaries = regional_service.get_regional_summary_for_date(
                    target_date=parsed_date, sort_by=sort_by
                )
            except Exception as e:
                logger.error(f"Initial data fetch failed: {e}")
                flash("Unable to fetch COVID-19 data. Please try again later.", "error")
                return render_template(
                    "error.html",
                    error_message="Unable to fetch COVID-19 data. Please try again later.",
                ), 503

        total_cases = sum(summary.total_cases for summary in regional_summaries)
        total_regions = len(regional_summaries)

        available_dates = regional_service.get_available_dates()

        return render_template(
            "index.html",
            regional_summaries=regional_summaries,
            total_cases=total_cases,
            total_regions=total_regions,
            current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            search_date=search_date,
            sort_by=sort_by,
            available_dates=available_dates[:30],
            historical_start=current_app.config["HISTORICAL_START_DATE"].strftime(
                "%Y-%m-%d"
            ),
        )

    except Exception as e:
        logger.error(f"Application error: {e}")
        flash("An internal error occurred. Please try again later.", "error")
        return render_template(
            "error.html",
            error_message="An internal error occurred. Please try again later.",
        ), 500


@main_bp.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template("error.html", error_message="Page not found."), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    logger.error(f"Internal server error: {error}")
    return render_template("error.html", error_message="Internal server error."), 500
