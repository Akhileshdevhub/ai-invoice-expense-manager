from app.extraction.fields import extract_amount, extract_date, extract_merchant, extract_currency


def test_extract_amount_prefers_grand_total_over_subtotal():
    text = "Swiggy\nItem 1  100\nItem 2  200\nSubtotal  300\nGrand Total Rs 350"
    amount, source = extract_amount(text)
    assert amount == 350
    assert source == "labeled_total"


def test_extract_amount_handles_currency_symbol_with_decimal():
    text = "Total: ₹450.00"
    amount, source = extract_amount(text)
    assert amount == 450.00


def test_extract_amount_falls_back_to_largest_number_when_unlabeled():
    text = "Some Shop\n120\n45\n300"
    amount, source = extract_amount(text)
    assert amount == 300
    assert source == "largest_amount"


def test_extract_amount_not_found_on_empty_text():
    amount, source = extract_amount("")
    assert amount is None
    assert source == "not_found"


def test_extract_date_handles_multiple_formats():
    assert extract_date("Date: 26 Aug 2026") == "2026-08-26"
    assert extract_date("26/08/2026") == "2026-08-26"
    assert extract_date("2026-08-26") == "2026-08-26"
    assert extract_date("Date: 26-08-2026") == "2026-08-26"


def test_extract_date_returns_none_when_absent():
    assert extract_date("No date on this receipt at all") is None


def test_extract_merchant_skips_boilerplate_header():
    lines = ["TAX INVOICE", "Swiggy Bangalore", "GSTIN: 12ABCDE"]
    assert extract_merchant(lines) == "Swiggy Bangalore"


def test_extract_merchant_returns_none_for_all_boilerplate():
    lines = ["TAX INVOICE", "www.example.com", "123456"]
    assert extract_merchant(lines) is None


def test_extract_currency_defaults_to_inr():
    assert extract_currency("Total 450") == "INR"


def test_extract_currency_detects_dollar():
    assert extract_currency("Total $45.00") == "USD"
