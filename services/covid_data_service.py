import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Tuple, Union

import requests
from flask import current_app
from sqlalchemy import func

from database import db
from models.cache import DataCache
from models.covid_data import CovidDataRecord
from models.data_classes import ProvinceData

logger = logging.getLogger(__name__)


class CovidDataService:
    """Enhanced service class for fetching and processing COVID-19 data."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def fetch_all_historical_data(self) -> List[ProvinceData]:
        """
        Fetch ALL historical COVID-19 data from the single JSON file.

        Returns:
            List of ProvinceData objects for all dates
        """
        data_url = current_app.config["COVID_DATA_URL_ALL"]

        try:
            logger.info(f"Fetching ALL historical data from {data_url}")
            response = requests.get(data_url, timeout=self.timeout)
            response.raise_for_status()

            raw_data = response.json()

            if not isinstance(raw_data, list):
                raise ValueError("Expected JSON array format")

            logger.info(f"Downloaded {len(raw_data)} total records")

            return self._parse_province_data(raw_data)

        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Invalid JSON response: {e}")

    def fetch_latest_data(self) -> List[ProvinceData]:
        """
        Fetch only the latest COVID-19 data.

        Returns:
            List of ProvinceData objects for the latest date
        """
        data_url = current_app.config["COVID_DATA_URL_LATEST"]

        try:
            logger.info(f"Fetching latest data from {data_url}")
            response = requests.get(data_url, timeout=self.timeout)
            response.raise_for_status()

            raw_data = response.json()

            if not isinstance(raw_data, list):
                raise ValueError("Expected JSON array format")

            logger.info(f"Downloaded {len(raw_data)} latest records")

            return self._parse_province_data(raw_data)

        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Invalid JSON response: {e}")

    def _parse_province_data(self, raw_data: List[Dict]) -> List[ProvinceData]:
        """Parse raw JSON data into ProvinceData objects."""
        province_data = []

        for record in raw_data:
            try:
                required_fields = [
                    "data",
                    "stato",
                    "codice_regione",
                    "denominazione_regione",
                    "codice_provincia",
                    "denominazione_provincia",
                    "totale_casi",
                ]

                missing_fields = []
                for field in required_fields:
                    if field not in record or record[field] is None:
                        missing_fields.append(field)

                if missing_fields:
                    logger.warning(
                        f"Missing required fields {missing_fields} in record"
                    )
                    continue

                denominazione_provincia = (
                    record.get("denominazione_provincia") or ""
                ).strip()

                if (
                    not denominazione_provincia
                    or "fase di definizione" in denominazione_provincia.lower()
                    or "aggiornamento" in denominazione_provincia.lower()
                ):
                    logger.debug(
                        f"Skipping problematic province: {denominazione_provincia}"
                    )
                    continue

                try:
                    codice_regione = int(record["codice_regione"])
                    codice_provincia = int(record["codice_provincia"])
                    totale_casi = max(0, int(record["totale_casi"]))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid numeric data in record: {e}")
                    continue

                province_data.append(
                    ProvinceData(
                        data=record["data"],
                        stato=record["stato"],
                        codice_regione=codice_regione,
                        denominazione_regione=(
                            record["denominazione_regione"] or ""
                        ).strip(),
                        codice_provincia=codice_provincia,
                        denominazione_provincia=denominazione_provincia,
                        sigla_provincia=(record.get("sigla_provincia") or "").strip(),
                        lat=float(record.get("lat", 0.0) or 0.0),
                        long=float(record.get("long", 0.0) or 0.0),
                        totale_casi=totale_casi,
                        note=(record.get("note") or "").strip(),
                        codice_nuts_1=(record.get("codice_nuts_1") or "").strip(),
                        codice_nuts_2=(record.get("codice_nuts_2") or "").strip(),
                        codice_nuts_3=(record.get("codice_nuts_3") or "").strip(),
                    )
                )

            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Skipping invalid record due to {e}")
                continue

        logger.info(f"Successfully parsed {len(province_data)} valid province records")
        return province_data

    def filter_data_by_date(
        self, province_data: List[ProvinceData], target_date: Union[date, str]
    ) -> List[ProvinceData]:
        """
        Filter province data for a specific date.

        Args:
            province_data: List of all ProvinceData objects
            target_date: Target date to filter for

        Returns:
            Filtered list of ProvinceData objects
        """
        if target_date == "latest":
            if not province_data:
                return []

            latest_timestamp = max(
                datetime.fromisoformat(record.data.replace("T", " ").replace("Z", ""))
                for record in province_data
            )
            target_date = latest_timestamp.date()

        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        filtered_data = []
        for record in province_data:
            record_date = datetime.fromisoformat(
                record.data.replace("T", " ").replace("Z", "")
            ).date()

            if record_date == target_date:
                filtered_data.append(record)

        logger.info(f"Filtered {len(filtered_data)} records for date {target_date}")
        return filtered_data

    def save_to_database(
        self, province_data: List[ProvinceData], cache_type: str = "full"
    ) -> Tuple[int, datetime]:
        """
        Save province data to the database using bulk insert for improved performance.

        Args:
            province_data: List of ProvinceData objects
            cache_type: Type of cache ('full' or 'latest')

        Returns:
            Tuple of (number of records saved, latest data timestamp)
        """
        if not province_data:
            raise ValueError("No data to save")

        try:
            with db.session.no_autoflush:
                saved_count = 0
                latest_timestamp = None

                if cache_type == "full":
                    logger.info("Clearing existing data for full refresh...")
                    db.session.query(CovidDataRecord).delete()
                    db.session.commit()

                    records_by_timestamp = {}
                    for province in province_data:
                        try:
                            timestamp = datetime.fromisoformat(
                                province.data.replace("T", " ").replace("Z", "")
                            )
                            if latest_timestamp is None or timestamp > latest_timestamp:
                                latest_timestamp = timestamp

                            key = f"{timestamp.isoformat()}_{province.codice_regione}_{province.codice_provincia}"
                            if key not in records_by_timestamp:
                                records_by_timestamp[key] = province
                        except Exception as e:
                            logger.warning(f"Skipping invalid province record: {e}")
                            continue

                    bulk_data = []
                    for province in records_by_timestamp.values():
                        bulk_data.append(self._prepare_record_for_insert(province))
                        saved_count += 1

                elif cache_type == "latest":
                    logger.info("Performing incremental update for latest data...")

                    existing_timestamps = set()
                    if province_data:
                        new_timestamps = []
                        for province in province_data:
                            try:
                                timestamp = datetime.fromisoformat(
                                    province.data.replace("T", " ").replace("Z", "")
                                )
                                new_timestamps.append(timestamp)
                            except Exception as e:
                                logger.warning(
                                    f"Invalid timestamp in province data: {e}"
                                )
                                continue

                        if new_timestamps:
                            latest_new_timestamp = max(new_timestamps)

                            existing_records = (
                                db.session.query(CovidDataRecord.data_timestamp)
                                .filter(
                                    CovidDataRecord.data_timestamp
                                    == latest_new_timestamp
                                )
                                .all()
                            )

                            existing_timestamps = {
                                record[0] for record in existing_records
                            }

                            if latest_new_timestamp in existing_timestamps:
                                logger.info(
                                    f"Latest data for {latest_new_timestamp} already exists, skipping insertion"
                                )

                                cache_record = DataCache.query.filter_by(
                                    cache_type=cache_type
                                ).first()
                                if cache_record:
                                    cache_record.last_fetch_time = datetime.now(
                                        timezone.utc
                                    )
                                    cache_record.last_data_timestamp = (
                                        latest_new_timestamp
                                    )
                                    db.session.commit()

                                return 0, latest_new_timestamp

                    records_by_timestamp = {}
                    for province in province_data:
                        try:
                            timestamp = datetime.fromisoformat(
                                province.data.replace("T", " ").replace("Z", "")
                            )

                            if timestamp in existing_timestamps:
                                logger.debug(
                                    f"Skipping duplicate timestamp: {timestamp}"
                                )
                                continue

                            if latest_timestamp is None or timestamp > latest_timestamp:
                                latest_timestamp = timestamp

                            key = f"{timestamp.isoformat()}_{province.codice_regione}_{province.codice_provincia}"
                            if key not in records_by_timestamp:
                                records_by_timestamp[key] = province
                        except Exception as e:
                            logger.warning(f"Skipping invalid province record: {e}")
                            continue

                    if records_by_timestamp:
                        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
                        old_records = (
                            db.session.query(CovidDataRecord)
                            .filter(CovidDataRecord.data_timestamp < cutoff_date)
                            .delete()
                        )

                        if old_records > 0:
                            logger.info(f"Cleaned up {old_records} old records")

                    bulk_data = []
                    for province in records_by_timestamp.values():
                        bulk_data.append(self._prepare_record_for_insert(province))
                        saved_count += 1

                if bulk_data:
                    db.session.bulk_insert_mappings(CovidDataRecord, bulk_data)
                    logger.info(f"Bulk inserted {len(bulk_data)} records")

                cache_record = DataCache.query.filter_by(cache_type=cache_type).first()

                if cache_type == "full":
                    min_date = db.session.query(
                        func.min(func.date(CovidDataRecord.data_timestamp))
                    ).scalar()
                    max_date = db.session.query(
                        func.max(func.date(CovidDataRecord.data_timestamp))
                    ).scalar()
                    date_range = (
                        f"{min_date} to {max_date}" if min_date and max_date else None
                    )
                else:
                    date_range = (
                        str(latest_timestamp.date()) if latest_timestamp else None
                    )

                if cache_record:
                    cache_record.last_fetch_time = datetime.now(timezone.utc)
                    cache_record.last_data_timestamp = latest_timestamp or datetime.now(
                        timezone.utc
                    )
                    cache_record.records_count = saved_count
                    cache_record.data_dates_range = date_range
                else:
                    cache_record = DataCache(
                        cache_type=cache_type,
                        last_fetch_time=datetime.now(timezone.utc),
                        last_data_timestamp=latest_timestamp
                        or datetime.now(timezone.utc),
                        records_count=saved_count,
                        data_dates_range=date_range,
                    )
                    db.session.add(cache_record)

                db.session.commit()
                logger.info(
                    f"Successfully saved {saved_count} records ({cache_type} cache)"
                )

                return saved_count, latest_timestamp or datetime.now(timezone.utc)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Database save failed: {e}")
            raise

    def _prepare_record_for_insert(self, province: ProvinceData) -> dict:
        """
        Helper method to prepare a province record for database insertion.
        """
        try:
            timestamp = datetime.fromisoformat(
                province.data.replace("T", " ").replace("Z", "")
            )

            return {
                "data_timestamp": timestamp,
                "stato": province.stato,
                "codice_regione": province.codice_regione,
                "denominazione_regione": province.denominazione_regione,
                "codice_provincia": province.codice_provincia,
                "denominazione_provincia": province.denominazione_provincia,
                "sigla_provincia": province.sigla_provincia,
                "lat": province.lat,
                "long": province.long,
                "totale_casi": province.totale_casi,
                "note": province.note,
                "codice_nuts_1": province.codice_nuts_1,
                "codice_nuts_2": province.codice_nuts_2,
                "codice_nuts_3": province.codice_nuts_3,
                "created_at": datetime.now(timezone.utc),
            }
        except Exception as e:
            logger.warning(f"Failed to prepare record for bulk insert: {e}")
            raise
