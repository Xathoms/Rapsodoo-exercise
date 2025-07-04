import os
from datetime import date


class Config:
    """Application configuration class."""

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///covid19_italy.db"
    )
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    COVID_DATA_URL_ALL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province.json"
    COVID_DATA_URL_LATEST = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province-latest.json"
    DATA_CACHE_MINUTES = int(os.environ.get("DATA_CACHE_MINUTES", "60"))
    REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))
    HISTORICAL_START_DATE = date(2020, 2, 24)
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    PORT = int(os.environ.get("PORT", 5000))


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
