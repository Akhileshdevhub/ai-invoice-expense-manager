"""One-off script (not part of the app) to capture real screenshots of the
running Streamlit app for the README/docs. Requires the app to already be
running locally (streamlit run main.py).
"""

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8501"
OUT_DIR = Path(__file__).resolve().parents[1] / "screenshots"


def click_nav(page, label: str):
    page.get_by_test_id("stRadio").get_by_text(label, exact=True).click()
    time.sleep(1.2)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(BASE_URL)
        time.sleep(2)

        # Dashboard (populated with seeded sample data)
        click_nav(page, "Dashboard")
        page.screenshot(path=str(OUT_DIR / "01_dashboard.png"), full_page=True)

        # Transactions table
        click_nav(page, "Transactions")
        page.screenshot(path=str(OUT_DIR / "02_transactions.png"), full_page=True)

        # Ask a Question
        click_nav(page, "Ask a Question")
        time.sleep(0.5)
        inputs = page.locator("input[type=text]")
        if inputs.count() > 0:
            inputs.last.fill("Food pe kitna kharcha hua?")
            page.get_by_role("button", name="Ask", exact=True).click()
            time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "03_ask_question.png"), full_page=True)

        # Upload Receipt (landing state)
        click_nav(page, "Upload Receipt")
        page.screenshot(path=str(OUT_DIR / "04_upload_landing.png"), full_page=True)

        # Upload + OCR extraction + verification screen (real upload, real OCR)
        sample_receipt = str(Path(__file__).resolve().parents[1] / "sample_receipts" / "swiggy_receipt.png")
        page.locator("input[type=file]").set_input_files(sample_receipt)
        time.sleep(3)
        page.screenshot(path=str(OUT_DIR / "05_ocr_verification.png"), full_page=True)

        browser.close()
    print(f"Saved screenshots to {OUT_DIR}")


if __name__ == "__main__":
    main()
