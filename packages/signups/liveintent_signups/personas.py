"""Persona definitions used for newsletter sign-ups.

Each persona is a self-consistent identity that we submit to publisher signup
forms. The alias is the local-part of the catch-all email; the address is a
generic US address with a real zip; fields are intentionally bland to avoid
triggering anti-bot heuristics.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    alias: str
    first_name: str
    last_name: str
    full_name: str
    address1: str
    city: str
    state: str
    zip_code: str
    country: str
    phone: str  # 10-digit US-style; many forms accept this
    gender: str  # "F" or "M"
    birth_year: int

    @property
    def email(self) -> str:
        return f"{self.alias}@clearmindskin.com"


PERSONAS: list[Persona] = [
    Persona(
        alias="r.alvarez",
        first_name="Rachel",
        last_name="Alvarez",
        full_name="Rachel Alvarez",
        address1="1450 NW 14th St",
        city="Miami",
        state="FL",
        zip_code="33125",
        country="US",
        phone="3055551234",
        gender="F",
        birth_year=1985,
    ),
    Persona(
        alias="j.chen",
        first_name="James",
        last_name="Chen",
        full_name="James Chen",
        address1="450 W 36th St",
        city="New York",
        state="NY",
        zip_code="10018",
        country="US",
        phone="2125551234",
        gender="M",
        birth_year=1980,
    ),
    Persona(
        alias="m.davis",
        first_name="Megan",
        last_name="Davis",
        full_name="Megan Davis",
        address1="2515 N Lincoln Ave",
        city="Chicago",
        state="IL",
        zip_code="60614",
        country="US",
        phone="3125551234",
        gender="F",
        birth_year=1990,
    ),
]


def by_alias(alias: str) -> Persona:
    for p in PERSONAS:
        if p.alias == alias:
            return p
    raise KeyError(f"Unknown persona alias: {alias}")
