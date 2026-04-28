from enum import StrEnum

class Vertical(StrEnum):
    SUPPLEMENTS = "supplements"
    FINANCE = "finance"
    INSURANCE = "insurance"
    SWEEPS = "sweeps"
    AUTO = "auto"
    SOLAR = "solar"
    HEALTH = "health"
    CRYPTO = "crypto"
    OTHER = "other"
    UNCLASSIFIED = "unclassified"

class VerticalSource(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"
