from app.classification.rules import categorize_by_rules


def test_known_merchant_maps_directly():
    category, method = categorize_by_rules("Swiggy", "")
    assert category == "Food"
    assert method == "merchant_match"


def test_keyword_in_text_maps_when_merchant_unknown():
    category, method = categorize_by_rules("Some Local Place", "Welcome to our restaurant, table 4")
    assert category == "Food"
    assert method == "keyword_match"


def test_unrecognized_text_defaults_to_other():
    category, method = categorize_by_rules("Totally Unknown Shop XYZ", "no useful keywords here")
    assert category == "Other"
    assert method == "default"


def test_electricity_bill_maps_to_utilities():
    category, method = categorize_by_rules("BSES", "Your electricity bill for this month")
    assert category == "Utilities"
