from datetime import date, datetime
from typing import Optional

from flask import current_app


def parse_date_input(date_input: str) -> Optional[date]:
    """
    Parse various date input formats.

    Args:
        date_input: Date string in various formats

    Returns:
        Parsed date object or None if invalid
    """
    if not date_input or date_input.lower() == "latest":
        return None

    date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"]

    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_input.strip(), fmt).date()

            historical_start = current_app.config.get("HISTORICAL_START_DATE")
            if parsed_date >= historical_start and parsed_date <= date.today():
                return parsed_date
        except ValueError:
            continue

    return None


def format_number(number: int) -> str:
    """
    Format number with thousands separators.

    Args:
        number: Number to format

    Returns:
        Formatted number string
    """
    return f"{number:,}"


def calculate_percentage(part: int, total: int) -> float:
    """
    Calculate percentage with safe division.

    Args:
        part: Part value
        total: Total value

    Returns:
        Percentage as float
    """
    return (part / total * 100) if total > 0 else 0.0


def is_date_in_range(check_date: date, start_date: date, end_date: date) -> bool:
    """
    Check if date is within range.

    Args:
        check_date: Date to check
        start_date: Range start date
        end_date: Range end date

    Returns:
        True if date is in range
    """
    return start_date <= check_date <= end_date
