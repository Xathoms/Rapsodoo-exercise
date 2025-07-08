import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, send_file
from utils import parse_date_input
from services import RegionalDataService
from services import ExcelExportService


logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)
regional_service = RegionalDataService()
excel_export_service = ExcelExportService()


@api_bp.route("/export/excel")
def api_export_excel():
    """
    Pure API endpoint for exporting regional data to Excel format.
    This endpoint handles all the business logic and file generation.
    """
    try:
        search_date = request.args.get("date", "latest")

        parsed_date = "latest"
        if search_date and search_date != "latest":
            parsed_date = parse_date_input(search_date)
            if parsed_date is None:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Invalid date format: {search_date}. Expected YYYY-MM-DD format.",
                    }
                ), 400

        excel_buffer, filename = excel_export_service.create_excel_export(parsed_date)

        logger.info(f"API Excel export completed: {filename}")

        return send_file(
            excel_buffer,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"API Excel export error: {e}")
        return jsonify(
            {"success": False, "error": "Failed to export data to Excel"}
        ), 500


@api_bp.route("/regions")
def api_regions():
    """
    API endpoint returning regional data as JSON.
    """
    try:
        search_date = request.args.get("date", "latest")
        limit = request.args.get("limit", type=int)
        format_type = request.args.get("format", "summary")

        parsed_date = "latest"
        if search_date and search_date != "latest":
            parsed_date = parse_date_input(search_date)
            if parsed_date is None:
                return jsonify(
                    {"success": False, "error": f"Invalid date format: {search_date}"}
                ), 400

        regional_summaries = regional_service.get_regional_summary_for_date(
            target_date=parsed_date, limit=limit
        )

        if format_type == "detailed":
            data = [summary.to_dict() for summary in regional_summaries]
        else:
            data = [
                {
                    "region_name": summary.region_name,
                    "total_cases": summary.total_cases,
                    "provinces_count": summary.provinces_count,
                    "last_updated": summary.last_updated,
                }
                for summary in regional_summaries
            ]

        return jsonify(
            {
                "success": True,
                "data": data,
                "metadata": {
                    "query_date": str(parsed_date),
                    "default_sort": "cases_desc_name_asc",
                    "total_regions": len(regional_summaries),
                    "total_cases": sum(
                        summary.total_cases for summary in regional_summaries
                    ),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "limit_applied": limit,
                    "format": format_type,
                },
            }
        )

    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@api_bp.route("/regions/<region_name>")
def api_region_detail(region_name):
    """API endpoint returning detailed data for a specific region."""
    try:
        search_date = request.args.get("date", "latest")

        parsed_date = "latest"
        if search_date and search_date != "latest":
            parsed_date = parse_date_input(search_date)
            if parsed_date is None:
                return jsonify(
                    {"success": False, "error": f"Invalid date format: {search_date}"}
                ), 400

        regional_summaries = regional_service.get_regional_summary_for_date(
            target_date=parsed_date
        )

        region_data = None
        for summary in regional_summaries:
            if summary.region_name.lower() == region_name.lower():
                region_data = summary
                break

        if not region_data:
            return jsonify(
                {"success": False, "error": f"Region '{region_name}' not found"}
            ), 404

        return jsonify(
            {
                "success": True,
                "data": region_data.to_dict(),
                "metadata": {
                    "query_date": str(parsed_date),
                    "region_name": region_name,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error(f"API error for region {region_name}: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@api_bp.route("/statistics")
def api_statistics():
    """API endpoint returning comprehensive statistics."""
    try:
        search_date = request.args.get("date", "latest")

        parsed_date = "latest"
        if search_date and search_date != "latest":
            parsed_date = parse_date_input(search_date)
            if parsed_date is None:
                return jsonify(
                    {"success": False, "error": f"Invalid date format: {search_date}"}
                ), 400

        stats = regional_service.get_region_statistics(parsed_date)

        if not stats:
            return jsonify(
                {"success": False, "error": "No data available for the specified date"}
            ), 404

        return jsonify(
            {
                "success": True,
                "data": {
                    "total_cases": stats["total_cases"],
                    "total_regions": stats["total_regions"],
                    "average_cases_per_region": stats["average_cases_per_region"],
                    "max_cases_region": stats["max_cases_region"],
                    "min_cases_region": stats["min_cases_region"],
                },
                "metadata": {
                    "query_date": str(parsed_date),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error(f"API statistics error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@api_bp.route("/dates")
def api_available_dates():
    """API endpoint returning available data dates."""
    try:
        limit = request.args.get("limit", default=50, type=int)

        available_dates = regional_service.get_available_dates()

        if limit and limit > 0:
            available_dates = available_dates[:limit]

        return jsonify(
            {
                "success": True,
                "data": {
                    "available_dates": [str(date) for date in available_dates],
                    "total_dates": len(available_dates),
                    "earliest_date": str(min(available_dates))
                    if available_dates
                    else None,
                    "latest_date": str(max(available_dates))
                    if available_dates
                    else None,
                },
                "metadata": {
                    "limit_applied": limit,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error(f"API dates error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@api_bp.route("/cache")
def api_cache_info():
    """API endpoint returning cache information."""
    try:
        cache_info = regional_service.get_cache_info()

        return jsonify(
            {
                "success": True,
                "data": cache_info,
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error(f"API cache info error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@api_bp.errorhandler(404)
def api_not_found(error):
    """API 404 error handler."""
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@api_bp.errorhandler(500)
def api_internal_error(error):
    """API 500 error handler."""
    logger.error(f"API internal server error: {error}")
    return jsonify({"success": False, "error": "Internal server error"}), 500
