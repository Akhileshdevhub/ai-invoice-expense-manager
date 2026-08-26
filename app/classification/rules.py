"""Rule-based category baseline: the default categorizer.

Two lookup tables, checked in order of specificity:

1. Known merchant -> category (highest confidence: "Swiggy" is always Food).
2. Keyword found anywhere in the OCR text -> category (broader net, catches
   merchants not in the table by what the receipt itself says).

This is the *default* categorizer (see docs/ML_PIPELINE.md for why),
not a fallback for the ML classifier — it's transparent, requires no
training data, and a wrong category is easy to trace back to the rule
that caused it.
"""

MERCHANT_CATEGORY = {
    "Swiggy": "Food", "Zomato": "Food", "Dominos": "Food", "Mcdonald'S": "Food",
    "Starbucks": "Food", "Kfc": "Food", "Faasos": "Food",
    "Uber": "Travel", "Ola": "Travel", "Irctc": "Travel", "Rapido": "Travel",
    "Indigo": "Travel", "Makemytrip": "Travel", "Redbus": "Travel",
    "Amazon": "Shopping", "Flipkart": "Shopping", "Myntra": "Shopping",
    "Ajio": "Shopping", "Nykaa": "Shopping",
    "Github": "Software", "Notion": "Software", "Figma": "Software",
    "Vercel": "Software", "Openai": "Software", "Adobe": "Software",
    "Udemy": "Education", "Coursera": "Education", "Byju'S": "Education",
    "Unacademy": "Education",
    "Apollo Pharmacy": "Healthcare", "Practo": "Healthcare", "Pharmeasy": "Healthcare",
    "Netflix": "Entertainment", "Spotify": "Entertainment", "Pvr": "Entertainment",
    "Bookmyshow": "Entertainment", "Hotstar": "Entertainment",
    "Bigbasket": "Groceries", "Blinkit": "Groceries", "Zepto": "Groceries",
    "Dmart": "Groceries",
    "Airtel": "Bills", "Jio": "Bills", "Vodafone": "Bills", "Vi": "Bills",
}

KEYWORD_CATEGORY = [
    (("restaurant", "cafe", "food court", "dhaba", "bakery", "pizza", "biryani"), "Food"),
    (("flight", "airlines", "airways", "train ticket", "metro card", "cab", "taxi", "fuel", "petrol", "diesel"), "Travel"),
    (("pharmacy", "hospital", "clinic", "medical store", "diagnostic", "medicine"), "Healthcare"),
    (("electricity", "water bill", "gas bill", "broadband", "wifi bill", "dth"), "Utilities"),
    (("house rent", "monthly rent", "rent receipt"), "Rent"),
    (("supermarket", "grocery", "kirana", "mart"), "Groceries"),
    (("movie", "cinema", "multiplex", "concert", "gaming"), "Entertainment"),
    (("tuition", "university", "college fee", "course fee", "workshop"), "Education"),
    (("subscription", "saas", "cloud hosting", "api credits", "software license"), "Software"),
    (("mobile recharge", "postpaid bill", "prepaid recharge"), "Bills"),
    (("clothing", "apparel", "electronics store", "furniture"), "Shopping"),
]

DEFAULT_CATEGORY = "Other"


def categorize_by_rules(merchant: str, raw_text: str) -> tuple[str, str]:
    """Return (category, method). method is 'merchant_match', 'keyword_match', or 'default'."""
    if merchant in MERCHANT_CATEGORY:
        return MERCHANT_CATEGORY[merchant], "merchant_match"

    lowered_text = f"{merchant} {raw_text}".lower()
    for keywords, category in KEYWORD_CATEGORY:
        if any(keyword in lowered_text for keyword in keywords):
            return category, "keyword_match"

    return DEFAULT_CATEGORY, "default"
