"""Generate synthetic receipt images for demos and OCR testing.

These are rendered text on a plain background using PIL — not photos of
real receipts (none were available or appropriate to use). They're
realistic enough to exercise the OCR + extraction pipeline end-to-end and
are clearly synthetic, which is the honest thing for a portfolio demo:
see docs/LIMITATIONS.md.

Run: python scripts/generate_sample_receipts.py
Output: sample_receipts/*.png
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "sample_receipts"

RECEIPTS = [
    {
        "filename": "swiggy_receipt.png",
        "lines": [
            "SWIGGY",
            "Order ID: 2026080145",
            "Date: 26 Aug 2026",
            "",
            "1x Chicken Biryani        320.00",
            "1x Cold Coffee             90.00",
            "1x Butter Naan             40.00",
            "",
            "Subtotal                  450.00",
            "Delivery Fee                0.00",
            "GST 5%                      0.00",
            "Grand Total Rs 450.00",
            "",
            "Payment Method: UPI",
        ],
    },
    {
        "filename": "uber_receipt.png",
        "lines": [
            "UBER INDIA SYSTEMS PVT LTD",
            "Trip Receipt",
            "Date: 12/08/2026",
            "",
            "Distance: 8.4 km",
            "Time: 22 min",
            "",
            "Fare Breakdown",
            "Base Fare                  60.00",
            "Distance Fare              190.00",
            "Booking Fee                 30.00",
            "",
            "Total Fare Rs 280.00",
            "Payment Method: Card",
        ],
    },
    {
        "filename": "amazon_invoice.png",
        "lines": [
            "TAX INVOICE",
            "Amazon Seller Services Pvt Ltd",
            "Order ID: 407-1234567-8901234",
            "Invoice Number: INV-2026-88213",
            "Date: 2026-08-05",
            "",
            "Wireless Mouse (Black)      999.00",
            "",
            "Taxable Value               847.00",
            "CGST 9%                      76.20",
            "SGST 9%                      76.20",
            "",
            "Grand Total Rs 999.00",
            "Payment Method: Net Banking",
        ],
    },
    {
        "filename": "bigbasket_receipt.png",
        "lines": [
            "BigBasket.com",
            "Order Receipt",
            "Date: 18 Aug 2026",
            "",
            "Atta 5kg                   285.00",
            "Milk Packet x4              88.00",
            "Vegetables Assorted        210.00",
            "Cooking Oil 1L              165.00",
            "",
            "Item Total                 748.00",
            "Delivery Charge              0.00",
            "Grand Total Rs 748.00",
            "Payment Method: UPI",
        ],
    },
    {
        "filename": "electricity_bill.png",
        "lines": [
            "BSES RAJDHANI POWER LIMITED",
            "Electricity Bill",
            "Bill No: EB2026080099",
            "Bill Date: 01 Aug 2026",
            "",
            "Units Consumed: 210 kWh",
            "Energy Charges             1450.00",
            "Fixed Charges                200.00",
            "",
            "Total Payable Rs 1650.00",
            "Due Date: 15 Aug 2026",
        ],
    },
]


def render_receipt(lines: list[str]) -> Image.Image:
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
    except OSError:
        font = ImageFont.load_default()

    line_height = 30
    width, height = 560, line_height * len(lines) + 60
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    y = 30
    for line in lines:
        draw.text((30, y), line, fill="black", font=font)
        y += line_height
    return img


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for receipt in RECEIPTS:
        img = render_receipt(receipt["lines"])
        path = OUTPUT_DIR / receipt["filename"]
        img.save(path)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
