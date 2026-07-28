"""`normalize_book` — human book names to the USFM IDs API.Bible requires.

The reference the model writes is the only thing standing between a citation
and the wrong scripture, so the cases here are the ones that would resolve to a
*different real book* rather than simply fail: ordinal prefixes, abbreviations,
and the names that collide.
"""

from lib.bible_books import normalize_book


def test_canonical_names_resolve():
    assert normalize_book("Genesis") == "GEN"
    assert normalize_book("Revelation") == "REV"
    # USFM diverges from the obvious three-letter truncation for several books;
    # these are the ones most often gotten wrong.
    assert normalize_book("Mark") == "MRK"
    assert normalize_book("John") == "JHN"
    assert normalize_book("Ezekiel") == "EZK"
    assert normalize_book("Philippians") == "PHP"
    assert normalize_book("Philemon") == "PHM"


def test_casing_and_trailing_punctuation_are_ignored():
    assert normalize_book("  gENeSiS  ") == "GEN"
    assert normalize_book("1 Cor.") == "1CO"
    assert normalize_book("Rom.,") == "ROM"


def test_ordinal_prefixes_fold_to_digits():
    # A model writing "II Timothy" and one writing "2 Tim" mean the same book.
    for form in ("2 Timothy", "II Timothy", "Second Timothy", "2nd Timothy"):
        assert normalize_book(form) == "2TI", form


def test_number_welded_to_name_is_split():
    assert normalize_book("1John") == "1JN"
    assert normalize_book("2Cor") == "2CO"


def test_ordinal_fold_does_not_swallow_single_token_books():
    # "I" maps to "1" only as a prefix — otherwise "Isaiah" and "Job" would be
    # mangled by the same rule.
    assert normalize_book("Isaiah") == "ISA"
    assert normalize_book("Job") == "JOB"


def test_song_of_songs_aliases_agree():
    for form in ("Song of Solomon", "Song of Songs", "Canticles", "SoS"):
        assert normalize_book(form) == "SNG", form


def test_ambiguous_jud_is_refused_but_full_names_resolve():
    # "Jud" reads as Jude, Judges, or Judith depending on the writer. Guessing
    # would mis-cite silently; the full names are unambiguous.
    assert normalize_book("Jud") is None
    assert normalize_book("Jude") == "JUD"
    assert normalize_book("Judges") == "JDG"
    assert normalize_book("Judith") == "JDT"


def test_deuterocanon_resolves():
    assert normalize_book("Sirach") == "SIR"
    assert normalize_book("Ecclesiasticus") == "SIR"
    assert normalize_book("1 Maccabees") == "1MA"
    assert normalize_book("Wisdom of Solomon") == "WIS"


def test_unknown_and_empty_input_return_none():
    assert normalize_book("Hezekiah") is None
    assert normalize_book("") is None
    assert normalize_book("   ") is None
    assert normalize_book(None) is None
