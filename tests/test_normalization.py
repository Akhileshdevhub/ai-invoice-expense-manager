from app.normalization.merchant import normalize_merchant


def test_strips_pvt_ltd_suffix():
    assert normalize_merchant("Swiggy Pvt Ltd") == "Swiggy"


def test_strips_internet_pvt_ltd_suffix():
    assert normalize_merchant("Swiggy Internet Pvt.") == "Swiggy"


def test_uppercase_name_normalizes_to_title_case():
    assert normalize_merchant("SWIGGY") == "Swiggy"


def test_alias_table_maps_known_variant():
    assert normalize_merchant("Amzn") == "Amazon"


def test_none_or_empty_returns_unknown_merchant():
    assert normalize_merchant(None) == "Unknown Merchant"
    assert normalize_merchant("   ") == "Unknown Merchant"


def test_fuzzy_matches_against_known_merchants_when_close():
    result = normalize_merchant("Swigy", known_merchants=["Swiggy", "Zomato"])
    assert result == "Swiggy"


def test_does_not_fuzzy_match_unrelated_merchant():
    result = normalize_merchant("Completely Different Store", known_merchants=["Swiggy", "Zomato"])
    assert result == "Completely Different Store"
