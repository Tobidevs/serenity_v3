"""Book and translation keys for API.Bible.

API.Bible takes USFM book IDs (`GEN`, `MRK`, `1JN`), not human book names, so
every reference has to be translated before it can be requested. Lookup is
alias-based rather than fuzzy on purpose: resolving "Jud" to Jude when the model
meant Judges would put the wrong scripture in a report with nothing to flag it.
Unknown input returns None so the tool can say so and let the model correct.

TRANSLATIONS maps an abbreviation to the opaque, per-account `bibleId`. Confirm
these against `GET /v1/bibles` with your key — an account only resolves the
Bibles it has licensed, and the Starter plan allows three.
"""

import re

TRANSLATIONS = {
    "KJV": "de4e12af7f28f599-01",   # public domain
    "ASV": "06125adad2d5898a-01",   # public domain
    "WEB": "9879dbb7cfe39e4d-01",   # public domain
    "NIV": "78a9f6124f344018-01",   # licensed; no commercial tier offered
    "NASB": "a761ca71e0b3ddcf-01",
    "CSB": "a556c5305ee15c3f-01",
    "ESV": "f421fe261da7624f-01",
    "NLT": "71c6eab17ae5b667-01",
    "NKJV": "de4e12af7f28f599-02",
}

DEFAULT_TRANSLATION = "KJV"

# Keys are lowercase, punctuation-free and single-spaced — the shape
# `normalize_book` produces. Ordinals fold to digits there, so numbered books
# only need their "1 x" spelling here.
BOOK_IDS = {
    # Old Testament
    "genesis": "GEN", "gen": "GEN", "gn": "GEN",
    "exodus": "EXO", "exod": "EXO", "exo": "EXO", "ex": "EXO",
    "leviticus": "LEV", "lev": "LEV", "lv": "LEV",
    "numbers": "NUM", "num": "NUM", "nm": "NUM",
    "deuteronomy": "DEU", "deut": "DEU", "deu": "DEU", "dt": "DEU",
    "joshua": "JOS", "josh": "JOS", "jos": "JOS",
    "judges": "JDG", "judg": "JDG", "jdg": "JDG",
    "ruth": "RUT", "rut": "RUT",
    "1 samuel": "1SA", "1 sam": "1SA", "1 sa": "1SA",
    "2 samuel": "2SA", "2 sam": "2SA", "2 sa": "2SA",
    "1 kings": "1KI", "1 kgs": "1KI", "1 ki": "1KI",
    "2 kings": "2KI", "2 kgs": "2KI", "2 ki": "2KI",
    "1 chronicles": "1CH", "1 chron": "1CH", "1 chr": "1CH",
    "2 chronicles": "2CH", "2 chron": "2CH", "2 chr": "2CH",
    "ezra": "EZR", "ezr": "EZR",
    "nehemiah": "NEH", "neh": "NEH",
    "esther": "EST", "esth": "EST", "est": "EST",
    "job": "JOB",
    "psalms": "PSA", "psalm": "PSA", "psa": "PSA", "ps": "PSA",
    "proverbs": "PRO", "prov": "PRO", "pro": "PRO",
    "ecclesiastes": "ECC", "eccl": "ECC", "ecc": "ECC", "qoheleth": "ECC",
    "song of solomon": "SNG", "song of songs": "SNG", "canticles": "SNG",
    "song": "SNG", "sos": "SNG",
    "isaiah": "ISA", "isa": "ISA",
    "jeremiah": "JER", "jer": "JER",
    "lamentations": "LAM", "lam": "LAM",
    "ezekiel": "EZK", "ezek": "EZK", "ezk": "EZK",
    "daniel": "DAN", "dan": "DAN",
    "hosea": "HOS", "hos": "HOS",
    "joel": "JOL", "jol": "JOL",
    "amos": "AMO", "amo": "AMO",
    "obadiah": "OBA", "obad": "OBA", "oba": "OBA",
    "jonah": "JON", "jon": "JON",
    "micah": "MIC", "mic": "MIC",
    "nahum": "NAM", "nah": "NAM",
    "habakkuk": "HAB", "hab": "HAB",
    "zephaniah": "ZEP", "zeph": "ZEP",
    "haggai": "HAG", "hag": "HAG",
    "zechariah": "ZEC", "zech": "ZEC",
    "malachi": "MAL", "mal": "MAL",

    # New Testament
    "matthew": "MAT", "matt": "MAT", "mat": "MAT", "mt": "MAT",
    "mark": "MRK", "mrk": "MRK", "mk": "MRK",
    "luke": "LUK", "luk": "LUK", "lk": "LUK",
    "john": "JHN", "jhn": "JHN", "jn": "JHN",
    "acts": "ACT", "act": "ACT",
    "romans": "ROM", "rom": "ROM",
    "1 corinthians": "1CO", "1 cor": "1CO", "1 co": "1CO",
    "2 corinthians": "2CO", "2 cor": "2CO", "2 co": "2CO",
    "galatians": "GAL", "gal": "GAL",
    "ephesians": "EPH", "eph": "EPH",
    # "phil" is conventionally Philippians, "philem" Philemon.
    "philippians": "PHP", "phil": "PHP", "php": "PHP",
    "colossians": "COL", "col": "COL",
    "1 thessalonians": "1TH", "1 thess": "1TH", "1 th": "1TH",
    "2 thessalonians": "2TH", "2 thess": "2TH", "2 th": "2TH",
    "1 timothy": "1TI", "1 tim": "1TI", "1 ti": "1TI",
    "2 timothy": "2TI", "2 tim": "2TI", "2 ti": "2TI",
    "titus": "TIT", "tit": "TIT",
    "philemon": "PHM", "philem": "PHM", "phlm": "PHM", "phm": "PHM",
    "hebrews": "HEB", "heb": "HEB",
    "james": "JAS", "jas": "JAS",
    "1 peter": "1PE", "1 pet": "1PE", "1 pe": "1PE",
    "2 peter": "2PE", "2 pet": "2PE", "2 pe": "2PE",
    "1 john": "1JN", "1 jn": "1JN",
    "2 john": "2JN", "2 jn": "2JN",
    "3 john": "3JN", "3 jn": "3JN",
    # No bare "jud" — it reads as Jude, Judges or Judith depending on who wrote
    # it, and picking one would quietly mis-cite.
    "jude": "JUD",
    "revelation": "REV", "rev": "REV", "apocalypse": "REV",

    # Deuterocanon. Absent from Protestant Bibles, where the API 404s — the
    # right answer for a comparative step, and why these are worth carrying.
    "tobit": "TOB", "judith": "JDT",
    "greek esther": "ESG", "additions to esther": "ESG",
    "wisdom": "WIS", "wisdom of solomon": "WIS",
    "sirach": "SIR", "ecclesiasticus": "SIR",
    "baruch": "BAR", "letter of jeremiah": "LJE",
    "prayer of azariah": "S3Y", "song of the three young men": "S3Y",
    "susanna": "SUS", "bel and the dragon": "BEL",
    "1 maccabees": "1MA", "1 macc": "1MA",
    "2 maccabees": "2MA", "2 macc": "2MA",
    "3 maccabees": "3MA", "4 maccabees": "4MA",
    "1 esdras": "1ES", "2 esdras": "2ES",
    "prayer of manasseh": "MAN", "psalm 151": "PS2",
}

_ORDINALS = {
    "1st": "1", "first": "1", "i": "1",
    "2nd": "2", "second": "2", "ii": "2",
    "3rd": "3", "third": "3", "iii": "3",
    "4th": "4", "fourth": "4", "iv": "4",
}

# "1john" -> split the welded digit off, but not when what follows is an
# ordinal tail: "2nd Timothy" must survive intact for the fold below.
_WELDED_NUMBER = re.compile(r"^([1-4])\s*(?!st\b|nd\b|rd\b|th\b)([a-z])")
_PUNCTUATION = re.compile(r"[^a-z0-9\s]")


def normalize_book(raw: str | None) -> str | None:
    """Resolve a human book name to its USFM ID, or None if unrecognized."""
    if not isinstance(raw, str):
        return None

    text = _PUNCTUATION.sub(" ", raw.lower())
    tokens = _WELDED_NUMBER.sub(r"\1 \2", text.strip()).split()
    if not tokens:
        return None

    # Fold a leading ordinal only when something follows, so "Isaiah" is not
    # read as the "I" prefix.
    if len(tokens) > 1 and tokens[0] in _ORDINALS:
        tokens[0] = _ORDINALS[tokens[0]]

    return BOOK_IDS.get(" ".join(tokens))
