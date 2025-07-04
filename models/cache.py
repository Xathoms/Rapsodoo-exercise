from database import db


class DataCache(db.Model):
    """Model for caching data fetch metadata."""

    __tablename__ = "data_cache"

    id = db.Column(db.Integer, primary_key=True)
    cache_type = db.Column(db.String(20), nullable=False, index=True)
    last_fetch_time = db.Column(db.DateTime, nullable=False)
    last_data_timestamp = db.Column(db.DateTime, nullable=False)
    records_count = db.Column(db.Integer, nullable=False)
    data_dates_range = db.Column(db.String(50))

    def __repr__(self):
        return f"<DataCache {self.cache_type} - {self.records_count} records>"

    def to_dict(self):
        """Convert cache record to dictionary."""
        return {
            "id": self.id,
            "cache_type": self.cache_type,
            "last_fetch_time": self.last_fetch_time.isoformat()
            if self.last_fetch_time
            else None,
            "last_data_timestamp": self.last_data_timestamp.isoformat()
            if self.last_data_timestamp
            else None,
            "records_count": self.records_count,
            "data_dates_range": self.data_dates_range,
        }
