import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, send_file

from services import ExcelExportService, RegionalDataService
from utils import parse_date_input

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
