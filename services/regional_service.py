import logging
from datetime import datetime, date, timezone
from typing import List, Union, Optional
from sqlalchemy import func

from database import db
from models.data_classes import RegionalSummary
from models.covid_data import CovidDataRecord
from models.cache import DataCache

logger = logging.getLogger(__name__)


class RegionalDataService:
    """Simplified service class for regional data aggregation and retrieval."""

    def __init__(self):
        pass

    def get_regional_summary_for_date(
        self,
        target_date: Union[date, str] = "latest",
        limit: Optional[int] = None,
    ) -> List[RegionalSummary]:
        """
        Get regional summary data for a specific date.
        Always returns data sorted by cases (descending) then by name (ascending) as default.
        """
        try:
            if target_date == "latest":
                latest_timestamp = db.session.query(
                    func.max(CovidDataRecord.data_timestamp)
                ).scalar()
                if not latest_timestamp:
                    return []
                query_timestamp = latest_timestamp
            else:
                if isinstance(target_date, str):
                    target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

                query_timestamp = (
                    db.session.query(CovidDataRecord.data_timestamp)
                    .filter(func.date(CovidDataRecord.data_timestamp) == target_date)
                    .first()
                )

                if not query_timestamp:
                    return []
                query_timestamp = query_timestamp[0]

            query = (
                db.session.query(
                    CovidDataRecord.denominazione_regione,
                    func.sum(CovidDataRecord.totale_casi).label("total_cases"),
                    func.count(CovidDataRecord.codice_provincia).label(
                        "provinces_count"
                    ),
                )
                .filter(CovidDataRecord.data_timestamp == query_timestamp)
                .group_by(CovidDataRecord.denominazione_regione)
                .order_by(
                    func.sum(CovidDataRecord.totale_casi).desc(),
                    CovidDataRecord.denominazione_regione.asc(),
                )
            )

            if limit:
                query = query.limit(limit)

            regional_data = query.all()

            summaries = []
            for region_name, total_cases, provinces_count in regional_data:
                summaries.append(
                    RegionalSummary(
                        region_name=region_name,
                        total_cases=total_cases,
                        provinces_count=provinces_count,
                        last_updated=query_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                )

            logger.info(
                f"Retrieved {len(summaries)} regional summaries for {target_date}"
            )
            return summaries

        except Exception as e:
            logger.error(f"Failed to retrieve regional summary: {e}")
            raise

    def should_refresh_data(self, cache_minutes: int = 60) -> bool:
        """Check if data should be refreshed based on cache age."""
        try:
            cache_record = DataCache.query.filter_by(cache_type="full").first()
            if not cache_record:
                return True

            cache_age = datetime.now(timezone.utc) - cache_record.last_fetch_time
            return cache_age.total_seconds() > (cache_minutes * 60)

        except Exception:
            return True

    def get_available_dates(self) -> List[date]:
        """Get list of dates for which we have data."""
        try:
            dates = (
                db.session.query(
                    func.distinct(func.date(CovidDataRecord.data_timestamp))
                )
                .order_by(func.date(CovidDataRecord.data_timestamp).desc())
                .all()
            )

            return [d[0] for d in dates]
        except Exception as e:
            logger.error(f"Failed to get available dates: {e}")
            return []

    def get_region_statistics(self, target_date: Union[date, str] = "latest") -> dict:
        """Get comprehensive statistics for all regions."""
        try:
            regional_summaries = self.get_regional_summary_for_date(target_date)

            if not regional_summaries:
                return {}

            total_cases = sum(summary.total_cases for summary in regional_summaries)
            total_regions = len(regional_summaries)

            case_values = [summary.total_cases for summary in regional_summaries]
            avg_cases = sum(case_values) / len(case_values) if case_values else 0
            max_cases = max(case_values) if case_values else 0
            min_cases = min(case_values) if case_values else 0

            return {
                "total_cases": total_cases,
                "total_regions": total_regions,
                "average_cases_per_region": round(avg_cases, 2),
                "max_cases_region": max_cases,
                "min_cases_region": min_cases,
                "regional_summaries": regional_summaries,
            }

        except Exception as e:
            logger.error(f"Failed to get region statistics: {e}")
            return {}

    def get_cache_info(self) -> dict:
        """Get information about data cache status."""
        try:
            full_cache = DataCache.query.filter_by(cache_type="full").first()
            latest_cache = DataCache.query.filter_by(cache_type="latest").first()

            cache_info = {
                "full_cache": full_cache.to_dict() if full_cache else None,
                "latest_cache": latest_cache.to_dict() if latest_cache else None,
                "needs_refresh": self.should_refresh_data(),
            }

            return cache_info

        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {}
