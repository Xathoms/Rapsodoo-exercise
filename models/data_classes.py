from dataclasses import dataclass


@dataclass
class RegionalSummary:
    """Data class for regional summary statistics."""

    region_name: str
    total_cases: int
    provinces_count: int
    last_updated: str

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "region_name": self.region_name,
            "total_cases": self.total_cases,
            "provinces_count": self.provinces_count,
            "last_updated": self.last_updated,
        }


@dataclass
class ProvinceData:
    """Data class for province COVID-19 data."""

    data: str
    stato: str
    codice_regione: int
    denominazione_regione: str
    codice_provincia: int
    denominazione_provincia: str
    sigla_provincia: str
    lat: float
    long: float
    totale_casi: int
    note: str
    codice_nuts_1: str = ""
    codice_nuts_2: str = ""
    codice_nuts_3: str = ""

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "data": self.data,
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
        }
