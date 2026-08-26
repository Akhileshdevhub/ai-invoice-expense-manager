"""Generate a small synthetic dataset for the category classifier.

This is NOT real receipt data — there is none available for a project
like this without violating someone's privacy. Each row is a short
templated snippet ("<merchant> <item phrase> <total phrase>") built to
resemble what OCR text for that category tends to contain. It's meant to
be just enough for a documented, honest ML experiment (see
docs/ML_PIPELINE.md) — not presented as a large or realistic corpus.

Run: python scripts/generate_training_data.py
Output: data/training_data.csv (columns: text, category)
"""

import csv
import random
from pathlib import Path

random.seed(42)  # reproducible dataset across runs

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "training_data.csv"

# category -> (merchants, item phrases, total phrase templates)
CATEGORY_TEMPLATES = {
    "Food": (
        ["Swiggy", "Zomato", "Dominos Pizza", "Cafe Coffee Day", "Barbeque Nation", "Faasos", "Behrouz Biryani"],
        ["Chicken Biryani x1", "Margherita Pizza", "Cold Coffee", "Veg Thali", "Butter Naan x2", "Paneer Tikka"],
        ["Grand Total Rs {amt}", "Total Amount INR {amt}", "Bill Total {amt}"],
    ),
    "Travel": (
        ["Uber", "Ola Cabs", "IRCTC", "IndiGo Airlines", "Rapido", "Indian Oil Petrol Pump", "MakeMyTrip"],
        ["Trip fare", "Train ticket PNR", "Flight booking", "Bike ride", "Fuel diesel 5L", "Hotel booking"],
        ["Total Fare Rs {amt}", "Amount Paid {amt}", "Grand Total INR {amt}"],
    ),
    "Shopping": (
        ["Amazon.in", "Flipkart", "Myntra", "Ajio", "Nykaa", "Reliance Digital"],
        ["Wireless Mouse", "Cotton T-Shirt", "Running Shoes", "Face Wash", "Bluetooth Speaker", "Backpack"],
        ["Order Total Rs {amt}", "Grand Total {amt}", "Amount Paid INR {amt}"],
    ),
    "Software": (
        ["GitHub Inc", "Notion Labs", "Figma Inc", "Vercel Inc", "OpenAI", "Adobe Creative Cloud"],
        ["Pro Plan Subscription", "Monthly API credits", "Team seat renewal", "Cloud hosting charges"],
        ["Total Amount USD {amt}", "Amount Charged {amt}", "Total Rs {amt}"],
    ),
    "Education": (
        ["Udemy", "Coursera", "BYJU'S", "Unacademy", "IIT Delhi Fee Office"],
        ["Course purchase", "Certification fee", "Semester tuition fee", "Workshop registration"],
        ["Total Paid Rs {amt}", "Amount Paid INR {amt}", "Grand Total {amt}"],
    ),
    "Healthcare": (
        ["Apollo Pharmacy", "Practo", "PharmEasy", "Max Hospital", "Fortis Clinic"],
        ["Medicine strip", "Doctor consultation fee", "Diagnostic test", "Health checkup package"],
        ["Total Amount Rs {amt}", "Bill Total {amt}", "Amount Paid INR {amt}"],
    ),
    "Utilities": (
        ["BSES Electricity", "Delhi Jal Board", "Airtel Broadband", "Mahanagar Gas"],
        ["Electricity bill units", "Water bill charges", "Broadband monthly charge", "Piped gas charges"],
        ["Total Payable Rs {amt}", "Amount Due {amt}", "Bill Amount INR {amt}"],
    ),
    "Entertainment": (
        ["PVR Cinemas", "BookMyShow", "Netflix", "Spotify Premium", "INOX Movies"],
        ["Movie ticket x2", "Popcorn combo", "Monthly subscription", "Concert ticket"],
        ["Total Amount Rs {amt}", "Amount Paid {amt}", "Grand Total INR {amt}"],
    ),
    "Rent": (
        ["Landlord Receipt", "NoBroker Rent Payment", "PG Accommodation"],
        ["Monthly house rent", "PG rent receipt", "Rent for flat"],
        ["Total Rent Paid Rs {amt}", "Amount Paid INR {amt}", "Rent Amount {amt}"],
    ),
    "Bills": (
        ["Jio Recharge", "Airtel Postpaid", "Vodafone Idea"],
        ["Mobile recharge plan", "Postpaid bill payment", "DTH recharge"],
        ["Total Amount Rs {amt}", "Bill Amount {amt}", "Amount Paid INR {amt}"],
    ),
    "Groceries": (
        ["BigBasket", "Blinkit", "Zepto", "DMart", "Reliance Fresh"],
        ["Atta 5kg", "Milk packet x4", "Vegetables assorted", "Rice 10kg", "Cooking oil 1L"],
        ["Grand Total Rs {amt}", "Order Total {amt}", "Amount Paid INR {amt}"],
    ),
    "Other": (
        ["City Municipal Office", "Local Stationery Shop", "Courier Service", "Salon"],
        ["Miscellaneous payment", "Service charge", "Stationery items", "Haircut service"],
        ["Total Rs {amt}", "Amount Paid {amt}", "Bill Total INR {amt}"],
    ),
}

SAMPLES_PER_CATEGORY = 20


def generate_row(merchants, items, totals) -> str:
    merchant = random.choice(merchants)
    item = random.choice(items)
    total = random.choice(totals).format(amt=random.choice([99, 149, 250, 399, 450, 599, 720, 999, 1200, 1850]))
    return f"{merchant}\n{item}\n{total}"


def main() -> None:
    rows = []
    for category, (merchants, items, totals) in CATEGORY_TEMPLATES.items():
        for _ in range(SAMPLES_PER_CATEGORY):
            rows.append((generate_row(merchants, items, totals), category))
    random.shuffle(rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "category"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic rows ({SAMPLES_PER_CATEGORY} per category, "
          f"{len(CATEGORY_TEMPLATES)} categories) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
