"""Band and CEFR calculations (approximate, for practice use only)."""
import math

# (minimum correct answers out of 40, band). Approximate Academic tables.
LISTENING = [(39, 9.0), (37, 8.5), (35, 8.0), (32, 7.5), (30, 7.0), (26, 6.5), (23, 6.0),
             (18, 5.5), (16, 5.0), (13, 4.5), (10, 4.0), (8, 3.5), (6, 3.0), (4, 2.5), (2, 2.0)]
READING = [(39, 9.0), (37, 8.5), (35, 8.0), (33, 7.5), (30, 7.0), (27, 6.5), (23, 6.0),
           (19, 5.5), (15, 5.0), (13, 4.5), (10, 4.0), (8, 3.5), (6, 3.0), (4, 2.5), (2, 2.0)]
TABLES = {"listening": LISTENING, "reading": READING}


def to_raw40(correct: int, total: int) -> int:
    """Scale a score to a 40-question test."""
    if total <= 0:
        return 0
    return round(correct / total * 40)


def raw_to_band(section: str, raw40: int) -> float:
    for minimum, band in TABLES[section]:
        if raw40 >= minimum:
            return band
    return 1.0 if raw40 >= 1 else 0.0


def round_band(value: float) -> float:
    """IELTS rounding: .25 -> .5, .75 -> next whole band."""
    return math.floor(value * 2 + 0.5) / 2


def band_to_cefr(band: float) -> str:
    if band >= 8.5:
        return "C2"
    if band >= 7.0:
        return "C1"
    if band >= 5.5:
        return "B2"
    if band >= 4.0:
        return "B1"
    if band >= 3.0:
        return "A2"
    return "A1"


def overall(bands: list[float]) -> float:
    return round_band(sum(bands) / len(bands))
