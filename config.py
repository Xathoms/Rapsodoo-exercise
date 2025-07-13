import os
from datetime import date


class Config:
    """Application configuration class."""

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///covid19_italy.db"
    )
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    COVID_DATA_URL_ALL = os.environ.get(
        "COVID_DATA_URL_ALL",
        "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province.json",
    )
    COVID_DATA_URL_LATEST = os.environ.get(
        "COVID_DATA_URL_LATEST",
        "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province-latest.json",
    )
    HISTORICAL_START_DATE = date.fromisoformat(
        os.environ.get("HISTORICAL_START_DATE", "2020-02-24")
    )
    DATA_CACHE_MINUTES = int(os.environ.get("DATA_CACHE_MINUTES", "60"))
    REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))
    DEBUG = os.environ.get("DEBUG", "True")
    PORT = int(os.environ.get("PORT", 5000))
    CACHE_FULL_REFRESH_HOURS = int(os.environ.get("CACHE_FULL_REFRESH_HOURS", "24"))
    CACHE_CLEANUP_DAYS = int(os.environ.get("CACHE_CLEANUP_DAYS", "7"))
    USER_INACTIVE_MINUTES = int(os.environ.get("USER_INACTIVE_MINUTES", "30"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", "16777216"))
    MISSING_DATES_CLEANUP_DAYS = int(os.environ.get("MISSING_DATES_CLEANUP_DAYS", "1"))


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    DATA_CACHE_MINUTES = 5


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    DATA_CACHE_MINUTES = 60


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
