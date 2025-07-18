import logging
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Set, Tuple, Union

from flask import current_app
from sqlalchemy import func

from database import db
from models.cache import DataCache
from models.covid_data import CovidDataRecord
from models.data_classes import RegionalSummary

logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache service for efficient COVID data management.

    This service implements intelligent caching strategies to minimize unnecessary
    data fetching while ensuring data freshness. It tracks missing dates and
    provides different refresh strategies based on data age and request patterns.

    Attributes:
        _known_missing_dates (Set[date]): Set of dates known to be unavailable
        _last_availability_check (Optional[datetime]): Last time availability was checked
    """

    def __init__(self):
        """Initialize the cache service with empty missing dates tracking."""
        self._known_missing_dates: Set[date] = set()
        self._last_availability_check: Optional[datetime] = None

    def should_refresh_data(self, cache_minutes: int = 60) -> Tuple[bool, str]:
        """
        Determine if data should be refreshed with correct cache type logic.

        Args:
            cache_minutes (int): Cache validity period in minutes.

        Returns:
            Tuple[bool, str]: (should_refresh, refresh_type)
        """
        try:
            now = datetime.now(timezone.utc)
            full_refresh_seconds = (
                current_app.config.get("CACHE_FULL_REFRESH_HOURS", 24) * 60 * 60
            )

            full_cache = DataCache.query.filter_by(cache_type="full").first()
            latest_cache = DataCache.query.filter_by(cache_type="latest").first()

            if not full_cache:
                logger.info("No full cache found, performing full refresh")
                return True, "full"

            full_last_fetch = full_cache.last_fetch_time
            if full_last_fetch.tzinfo is None:
                full_last_fetch = full_last_fetch.replace(tzinfo=timezone.utc)

            full_cache_age = now - full_last_fetch

            if full_cache_age.total_seconds() > full_refresh_seconds:
                logger.info(
                    f"Full cache is older than {current_app.config.get('CACHE_FULL_REFRESH_HOURS', 24)} hours, performing full refresh"
                )
                return True, "full"

            if latest_cache:
                latest_last_fetch = latest_cache.last_fetch_time
                if latest_last_fetch.tzinfo is None:
                    latest_last_fetch = latest_last_fetch.replace(tzinfo=timezone.utc)

                latest_cache_age = now - latest_last_fetch

                if latest_cache_age.total_seconds() > (cache_minutes * 60):
                    logger.info(
                        f"Latest cache is older than {cache_minutes} minutes, performing incremental refresh"
                    )
                    return True, "incremental"
            else:
                if full_cache_age.total_seconds() > (cache_minutes * 60):
                    logger.info("No latest cache found, performing incremental refresh")
                    return True, "incremental"

            logger.info("Cache is fresh, no refresh needed")
            return False, "none"

        except Exception as e:
            logger.error(f"Error checking cache status: {e}")
            return True, "full"

    def is_date_known_missing(self, target_date: Union[date, str]) -> bool:
        """
        Check if a specific date is already known to be missing from the dataset.

        This helps avoid repeated API calls for dates that don't exist in the
        upstream data source, improving performance and reducing unnecessary load.

        Args:
            target_date (Union[date, str]): Date to check, either date object or 'latest'

        Returns:
            bool: True if the date is known to be missing, False otherwise
        """
        if isinstance(target_date, str):
            if target_date == "latest":
                return False
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        return target_date in self._known_missing_dates

    def mark_date_as_missing(self, target_date: Union[date, str]) -> None:
        """
        Mark a specific date as missing to avoid future fetch attempts.

        This method is called when a date is confirmed to be unavailable in the
        dataset after a fetch attempt, preventing repeated API calls for the same date.

        Args:
            target_date (Union[date, str]): Date to mark as missing

        """
        if isinstance(target_date, str) and target_date != "latest":
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            self._known_missing_dates.add(target_date)
            logger.debug(f"Marked date as missing: {target_date}")

    def get_cache_strategy_for_date(self, target_date: Union[date, str]) -> str:
        """
        Determine the optimal caching strategy for retrieving data for a specific date.

        Analyzes the requested date against existing cache, known missing dates,
        and data availability patterns to choose the most efficient approach.

        Args:
            target_date (Union[date, str]): Target date for data retrieval

        Returns:
            str: Recommended strategy - one of:
                - 'use_cache': Data is available in cache
                - 'fetch_incremental': Fetch only recent data
                - 'fetch_full': Fetch complete historical data
                - 'date_missing': Date is known to be unavailable
        """
        if target_date == "latest":
            should_refresh, refresh_type = self.should_refresh_data()
            if not should_refresh:
                return "use_cache"
            return f"fetch_{refresh_type}"

        if self.is_date_known_missing(target_date):
            return "date_missing"

        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        existing_data = (
            db.session.query(CovidDataRecord)
            .filter(func.date(CovidDataRecord.data_timestamp) == target_date)
            .first()
        )

        if existing_data:
            return "use_cache"

        should_refresh, refresh_type = self.should_refresh_data()

        days_ago = (date.today() - target_date).days
        if days_ago > 7:
            available_dates = self._get_available_date_range()
            if available_dates:
                earliest_date, latest_date = available_dates
                if isinstance(earliest_date, str):
                    earliest_date = datetime.strptime(earliest_date, "%Y-%m-%d").date()
                if target_date < earliest_date:
                    self.mark_date_as_missing(target_date)
                    return "date_missing"

        return f"fetch_{refresh_type}"

    def _get_available_date_range(self) -> Optional[Tuple[date, date]]:
        """
        Get the range of dates available in the local database.

        This helps determine if a requested date falls outside the available
        data range, allowing for early rejection of impossible requests.

        Returns:
            Optional[Tuple[date, date]]: (earliest_date, latest_date) if data exists,
                                    None if no data is available

        """
        try:
            result = db.session.query(
                func.min(func.date(CovidDataRecord.data_timestamp)),
                func.max(func.date(CovidDataRecord.data_timestamp)),
            ).first()

            if result and result[0] and result[1]:
                return (result[0], result[1])
            return None
        except Exception as e:
            logger.error(f"Failed to get available date range: {e}")
            return None

    def cleanup_old_missing_dates(self) -> None:
        """
        Clean up old missing date entries to allow for re-checking.

        Removes dates marked as missing that are older than 24 hours,
        as new data might have been added to the upstream source.
        This prevents permanent blacklisting of dates that might become available.

        Should be called periodically (e.g., daily) to maintain cache accuracy.
        """
        cleanup_days = current_app.config.get("MISSING_DATES_CLEANUP_DAYS", 1)

        cutoff = date.today() - timedelta(days=cleanup_days)
        initial_count = len(self._known_missing_dates)

        self._known_missing_dates = {d for d in self._known_missing_dates if d > cutoff}

        cleaned_count = initial_count - len(self._known_missing_dates)
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old missing date entries")


class RegionalDataService:
    """
    Intelligent regional data service with optimized caching strategies.

    This service combines the CacheService with regional data retrieval
    to provide efficient, cache-aware data access. It automatically handles
    cache strategies, data refresh decisions, and graceful fallbacks.

    Features:
    - Automatic cache strategy selection
    - Intelligent refresh decisions
    - Graceful error handling with fallbacks
    - Missing date tracking and management
    - Status reporting for debugging and monitoring

    Attributes:
        cache_service (CacheService): Cache management service
    """

    def __init__(self):
        """Initialize the smart regional service with cache management."""
        self.cache_service = CacheService()

    def get_regional_summary_smart(
        self, target_date: Union[date, str] = "latest", covid_service=None
    ) -> Tuple[List[RegionalSummary], str]:
        """
        Retrieve regional summary data using intelligent caching strategies.

        This method automatically determines the best approach for data retrieval
        based on cache status, data availability, and request patterns. It provides
        detailed status information for monitoring and debugging.

        Args:
            target_date (Union[date, str]): Target date for data retrieval.
                                        Use 'latest' for most recent data.
            covid_service: COVID data service instance for fetching fresh data

        Returns:
            Tuple[List[RegionalSummary], str]: (regional_data, status_message)

            regional_data: List of regional summary objects with case data
            status_message: Human-readable status describing the operation performed

        Status Messages:
            - "Using cached data": Data retrieved from local cache
            - "Data refreshed (incremental/full)": Fresh data fetched successfully
            - "Date {date} is known to be unavailable": Date is in missing list
            - "No data available for {date} after refresh": Date confirmed missing
            - "Using cached data (refresh failed)": Fallback to cache after error
            - "Data unavailable: {error}": Error occurred and no fallback available
        """
        strategy = self.cache_service.get_cache_strategy_for_date(target_date)

        if strategy == "date_missing":
            return [], f"Date {target_date} is known to be unavailable"

        if strategy == "use_cache":
            data = self._get_from_cache(target_date)
            if data:
                return data, "Using cached data"

        if strategy.startswith("fetch_") and covid_service:
            refresh_type = strategy.split("_")[1]

            try:
                if refresh_type == "incremental":
                    logger.info("Performing incremental data refresh for latest data")
                    latest_data = covid_service.fetch_latest_data()

                    if latest_data:
                        saved_count, latest_timestamp = covid_service.save_to_database(
                            latest_data, "latest"
                        )

                        if saved_count > 0:
                            logger.info(f"Saved {saved_count} new records")
                        else:
                            logger.info("No new data to save (already up to date)")
                    else:
                        logger.warning("No data returned from incremental fetch")

                elif refresh_type == "full":
                    logger.info("Performing full historical data refresh")
                    all_data = covid_service.fetch_all_historical_data()

                    if all_data:
                        saved_count, latest_timestamp = covid_service.save_to_database(
                            all_data, "full"
                        )
                        logger.info(f"Full refresh completed: {saved_count} records")
                    else:
                        logger.warning("No data returned from full fetch")

                data = self._get_from_cache(target_date)
                if data:
                    return data, f"Data refreshed ({refresh_type})"
                else:
                    self.cache_service.mark_date_as_missing(target_date)
                    return [], f"No data available for {target_date} after refresh"

            except Exception as e:
                logger.error(f"Data refresh failed: {e}")

                data = self._get_from_cache(target_date)
                if data:
                    return data, "Using cached data (refresh failed)"
                return [], f"Data unavailable: {str(e)}"

        data = self._get_from_cache(target_date)
        if data:
            return data, "Using cached data (no refresh service)"

        return [], "No data available"

    def _get_from_cache(self, target_date: Union[date, str]) -> List[RegionalSummary]:
        """
        Retrieve regional summary data from local database cache.

        This method handles the database queries needed to aggregate provincial
        data into regional summaries, with proper date filtering and sorting.

        Args:
            target_date (Union[date, str]): Target date for data retrieval

        Returns:
            List[RegionalSummary]: List of regional summary objects sorted by
                                total cases (descending) then region name (ascending)

        """
        try:
            if target_date == "latest":
                latest_timestamp = db.session.query(
                    func.max(CovidDataRecord.data_timestamp)
                ).scalar()

                if not latest_timestamp:
                    logger.warning("No data found in database")
                    return []

                query_timestamp = latest_timestamp

            else:
                if isinstance(target_date, str):
                    try:
                        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
                    except ValueError:
                        logger.error(f"Invalid date format: {target_date}")
                        return []

                query_timestamp = (
                    db.session.query(CovidDataRecord.data_timestamp)
                    .filter(func.date(CovidDataRecord.data_timestamp) == target_date)
                    .first()
                )

                if not query_timestamp:
                    logger.info(f"No data found for date: {target_date}")
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

            logger.debug(f"Retrieved {len(summaries)} regional summaries from cache")
            return summaries

        except Exception as e:
            logger.error(f"Failed to retrieve data from cache: {e}")
            return []

    def get_regional_summary_for_date(
        self, target_date: Union[date, str] = "latest", limit: Optional[int] = None
    ) -> List[RegionalSummary]:
        """
        Get regional summary for a specific date with smart caching.
        """

        summaries, status = self.get_regional_summary_smart(target_date)

        if limit and limit > 0:
            summaries = summaries[:limit]

        logger.info(
            f"Retrieved {len(summaries)} regional summaries for {target_date} - {status}"
        )
        return summaries

    def get_region_statistics(
        self, target_date: Union[date, str] = "latest"
    ) -> Optional[dict]:
        """Get comprehensive statistics for regions."""
        summaries = self.get_regional_summary_for_date(target_date)

        if not summaries:
            return None

        total_cases = sum(summary.total_cases for summary in summaries)
        total_regions = len(summaries)

        if total_regions == 0:
            return None

        average_cases = total_cases / total_regions
        max_region = max(summaries, key=lambda x: x.total_cases)
        min_region = min(summaries, key=lambda x: x.total_cases)

        return {
            "total_cases": total_cases,
            "total_regions": total_regions,
            "average_cases_per_region": round(average_cases, 2),
            "max_cases_region": {
                "name": max_region.region_name,
                "cases": max_region.total_cases,
            },
            "min_cases_region": {
                "name": min_region.region_name,
                "cases": min_region.total_cases,
            },
        }

    def get_available_dates(self, limit: Optional[int] = None) -> List[date]:
        """Get list of available dates in the database."""
        try:
            query = db.session.query(
                func.distinct(func.date(CovidDataRecord.data_timestamp))
            ).order_by(func.date(CovidDataRecord.data_timestamp).desc())

            if limit:
                query = query.limit(limit)

            dates = query.all()
            return [d[0] for d in dates]
        except Exception as e:
            logger.error(f"Failed to get available dates: {e}")
            return []

    def get_cache_info(self) -> dict:
        """Get information about current cache status."""
        try:
            cache_records = DataCache.query.all()
            cache_info = {}

            for record in cache_records:
                cache_info[record.cache_type] = record.to_dict()

            return cache_info
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {}
