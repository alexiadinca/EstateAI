"""Rule-based reading of Romanian listing text.

Sellers describe properties in free text, for example "Apartament 2 camere, 54 mp utili,
etaj 3/4, bloc din 1985, fara lift". These rules recognise the common phrasings. They are
deterministic, so the same text always gives the same result, and every value is shown to the
user for review. Anything the rules do not recognise stays unknown.

Matching runs on a folded copy of the text: lowercase and without diacritics, so "Bucureşti",
"București" and "bucuresti" are treated alike.
"""

import re
import unicodedata
from decimal import Decimal

from app.extraction.listing_data import ListingData

ORIGIN = "description"

NUMBER_WORDS = {"o": 1, "una": 1, "doua": 2, "trei": 3, "patru": 4, "cinci": 5, "sase": 6}
# Thousands may be written with spaces or dots: 123 000, 123.000 or 123000.
AMOUNT = r"\d{1,3}(?:[ .]\d{3})+|\d{3,9}"
YEAR = r"(?:18|19|20)\d\d"
DECIMAL_AREA = r"\d{2,4}(?:[.,]\d{1,2})?"


def fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def _amount(raw: str) -> Decimal:
    return Decimal(re.sub(r"[ .]", "", raw))


def _area(raw: str) -> Decimal:
    return Decimal(raw.replace(",", "."))


def parse_listing_text(text: str) -> ListingData:
    found = ListingData(description=text)
    folded = fold(text)

    found.add("property_type", _property_type(folded), ORIGIN)
    found.transaction_type = _transaction_type(folded)
    found.city_name = _city(folded)
    found.city_origin = ORIGIN if found.city_name else None
    found.add("neighborhood", _neighborhood(text), ORIGIN)
    found.add("rooms", _rooms(folded), ORIGIN)
    found.add("usable_area_m2", _usable_area(folded), ORIGIN)
    found.add("construction_year", _construction_year(folded), ORIGIN)
    found.add("structure", _structure(folded), ORIGIN)
    found.add("condition", _condition(folded), ORIGIN)
    found.add("has_balcony", _stated(folded, "balcon(?:ul|ane)?", "balcon"), ORIGIN)
    found.add(
        "has_parking",
        _stated(folded, r"(?:loc\s+de\s+)?parcare|garaj", "(?:loc de )?parcare"),
        ORIGIN,
    )

    # The apartment floor and the lift are only meaningful for apartments; in a house
    # description "etaj" usually names a level of the house.
    if found.values.get("property_type") != "house":
        floor, total_floors = _floor(folded)
        found.add("floor", floor, ORIGIN)
        found.add("total_floors", total_floors, ORIGIN)
        found.add("has_elevator", _stated(folded, "lift|ascensor", "lift"), ORIGIN)

    amount, currency = _price(folded)
    found.add_price(amount, currency, ORIGIN)
    return found


def _property_type(folded: str) -> str | None:
    # "Apartament in casa tip duplex" is an apartment, so apartment words are checked first.
    if re.search(r"\b(?:apartament\w*|garsonier\w*|studio)\b", folded):
        return "apartment"
    if re.search(r"\b(?:casa|case|vila|duplex)\b", folded):
        return "house"
    return None


def _transaction_type(folded: str) -> str | None:
    rent = re.search(r"\b(?:de\s+inchiriat|inchiriez|inchiriere|chiri[ae])\b|/\s*luna\b", folded)
    sale = re.search(r"\b(?:de\s+vanzare|vand|vanzare|se\s+vinde)\b", folded)
    if rent and not sale:
        return "rent"
    if sale and not rent:
        return "sale"
    return None


def _city(folded: str) -> str | None:
    if re.search(r"\bcraiova\b", folded):
        return "Craiova"
    if re.search(r"\bbucuresti\b|\bsector(?:ul)?\s*[1-6]\b", folded):
        return "Bucharest"
    return None


def _neighborhood(text: str) -> str | None:
    """Capitalised place name after "zona" or "cartier", read from the original text."""
    word = r"[A-ZĂÂÎȘȚŞŢ][\w'’-]*"
    match = re.search(
        rf"\b(?:[Zz]ona|[Cc]artier(?:ul)?)\s+({word}(?:\s+(?:lui\s+)?{word}){{0,2}})", text
    )
    return match.group(1).strip() if match else None


def _rooms(folded: str) -> int | None:
    if match := re.search(r"\b(\d{1,2})\s*(?:camere|cam)\b", folded):
        return int(match.group(1))
    if match := re.search(r"\b(o|una|doua|trei|patru|cinci|sase)\s+camer[ae]\b", folded):
        return NUMBER_WORDS[match.group(1)]
    if re.search(r"\b(?:garsoniera|studio)\b", folded):
        return 1
    return None


def _usable_area(folded: str) -> Decimal | None:
    # Only areas explicitly described as usable; built or land areas are different measures.
    patterns = [
        rf"\b({DECIMAL_AREA})\s*(?:mp|m2|metri\s+patrati)\s*(?:utili|utila|util)\b",
        rf"\bsuprafata\s+utila\s*(?:de\s*)?:?\s*({DECIMAL_AREA})",
    ]
    for pattern in patterns:
        if match := re.search(pattern, folded):
            return _area(match.group(1))
    return None


def _floor(folded: str) -> tuple[int | None, int | None]:
    """Apartment floor and the highest floor of the building, when stated."""
    if match := re.search(r"\betaj(?:ul)?\s*:?\s*(\d{1,2})\s*(?:/|din)\s*(\d{1,2})\b", folded):
        return int(match.group(1)), int(match.group(2))
    total_floors = None
    if match := re.search(r"\bp\s*\+\s*(\d{1,2})\b", folded):
        total_floors = int(match.group(1))
    if match := re.search(r"\betaj(?:ul)?\s*:?\s*(\d{1,2})\b", folded):
        return int(match.group(1)), total_floors
    if re.search(r"\b(?:situat\s+)?la\s+parter\b|\betaj(?:ul)?\s*:?\s*parter\b", folded):
        return 0, total_floors
    if re.search(r"\bla\s+demisol\b", folded):
        return -1, total_floors
    return None, total_floors


def _construction_year(folded: str) -> int | None:
    pattern = (
        r"\b(?:an(?:ul)?\s+(?:de\s+)?constructi(?:e|a)|construit(?:a)?\s+(?:in\s+)?(?:anul\s+)?"
        rf"|bloc\s+(?:construit\s+)?(?:din|in)\s+(?:anul\s+)?)\s*:?\s*({YEAR})\b"
    )
    if match := re.search(pattern, folded):
        return int(match.group(1))
    return None


def _structure(folded: str) -> str | None:
    match = re.search(
        r"\b(?:structura(?:\s+de\s+rezistenta)?|construit[ae]?|bloc|casa|din)\s+(?:din\s+)?"
        r"(beton(?:\s+armat)?|caramida|bca|lemn|metal)\b",
        folded,
    )
    if not match:
        return None
    material = match.group(1)
    if material.startswith("beton"):
        return "concrete"
    return {"caramida": "brick", "bca": "aerated_concrete", "lemn": "wood", "metal": "metal"}[
        material
    ]


def _condition(folded: str) -> str | None:
    if re.search(r"\bnecesita\s+(?:renovare|reparatii|modernizare)|\bde\s+renovat\b", folded):
        return "needs_renovation"
    if re.search(r"\b(?:proaspat\s+|complet\s+)?renovat[a]?\b", folded):
        return "renovated"
    if re.search(r"\b(?:constructie|bloc|imobil|casa)\s+noua?\b", folded):
        return "new"
    if re.search(r"\bstare\s+(?:foarte\s+)?buna\b", folded):
        return "good"
    return None


def _stated(folded: str, present_pattern: str, absent_pattern: str) -> bool | None:
    """True when mentioned, False when stated as missing ("fara lift"), None when silent."""
    if re.search(rf"\bfara\s+{absent_pattern}\b", folded):
        return False
    if re.search(rf"\b(?:{present_pattern})\b", folded):
        return True
    return None


def _price(folded: str) -> tuple[Decimal | None, str | None]:
    currency = r"(euro|eur|€|lei|ron)(?=\W|$)"
    for pattern in (
        rf"\b(?:pret|valoare)\w*\s*:?\s*({AMOUNT})\s*{currency}",
        rf"(?<![\d.])({AMOUNT})\s*{currency}",
    ):
        if match := re.search(pattern, folded):
            code = "RON" if match.group(2) in ("lei", "ron") else "EUR"
            return _amount(match.group(1)), code
    return None, None
