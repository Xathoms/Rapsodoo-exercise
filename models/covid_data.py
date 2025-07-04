from datetime import datetime
from database import db


class CovidDataRecord(db.Model):
    """SQLAlchemy model for storing COVID-19 province data."""

    __tablename__ = "covid_data_records"

    id = db.Column(db.Integer, primary_key=True)
    data_timestamp = db.Column(db.DateTime, nullable=False, index=True)
    stato = db.Column(db.String(10), nullable=False)
    codice_regione = db.Column(db.Integer, nullable=False, index=True)
    denominazione_regione = db.Column(db.String(100), nullable=False, index=True)
    codice_provincia = db.Column(db.Integer, nullable=False)
    denominazione_provincia = db.Column(db.String(100), nullable=False)
    sigla_provincia = db.Column(db.String(10))
    lat = db.Column(db.Float)
    long = db.Column(db.Float)
    totale_casi = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text)
    codice_nuts_1 = db.Column(db.String(10))
    codice_nuts_2 = db.Column(db.String(10))
    codice_nuts_3 = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CovidDataRecord {self.denominazione_regione}/{self.denominazione_provincia} - {self.totale_casi}>"

    def to_dict(self):
        """Convert record to dictionary."""
        return {
            "id": self.id,
            "data_timestamp": self.data_timestamp.isoformat()
            if self.data_timestamp
            else None,
            "stato": self.stato,
            "codice_regione": self.codice_regione,
            "denominazione_regione": self.denominazione_regione,
            "codice_provincia": self.codice_provincia,
            "denominazione_provincia": self.denominazione_provincia,
            "sigla_provincia": self.sigla_provincia,
            "lat": self.lat,
            "long": self.long,
            "totale_casi": self.totale_casi,
            "note": self.note,
            "codice_nuts_1": self.codice_nuts_1,
            "codice_nuts_2": self.codice_nuts_2,
            "codice_nuts_3": self.codice_nuts_3,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
