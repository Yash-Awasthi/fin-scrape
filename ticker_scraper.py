import json
import time
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def build_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def dismiss_overlays(driver):
    """Click any visible consent / onboarding buttons."""
    labels = ["Done", "Accept all", "Accept All", "Reject all", "Close", "Got it"]
    for label in labels:
        try:
            btn = driver.find_element(
                By.XPATH, f"//button[normalize-space()='{label}']"
            )
            btn.click()
            print(f"  Dismissed: '{label}' button")
            time.sleep(0.8)
        except Exception:
            pass


def wait_for_rows(driver, timeout=20):
    """
    Wait until ticker cells appear.
    KEY FIX: attribute is data-testid-cell, NOT data-testid (confirmed from DOM in image).
    """
    for i in range(timeout):
        rows = driver.find_elements(By.CSS_SELECTOR, 'td[data-testid-cell="ticker"]')
        if rows:
            print(f"  Rows detected: {len(rows)}")
            return rows
        if i % 5 == 4:
            dismiss_overlays(driver)
        print(f"  Waiting... ({i + 1}s)")
        time.sleep(1)
    return []


def parse_page(driver):
    """Extract (ticker_symbol, company_name) pairs from the current page."""
    ticker_cells = driver.find_elements(
        By.CSS_SELECTOR, 'td[data-testid-cell="ticker"]'
    )
    name_cells = driver.find_elements(
        By.CSS_SELECTOR, 'td[data-testid-cell="companyshortname.raw"]'
    )

    pairs = []
    for t_cell, n_cell in zip(ticker_cells, name_cells):
        # Ticker: grab from nested <span class="symbol ..."> to avoid extra text
        try:
            symbol = t_cell.find_element(By.CSS_SELECTOR, "span.symbol").text.strip()
        except Exception:
            symbol = t_cell.text.strip().split()[0]  # fallback

        # Company name: prefer title attribute on inner div (most reliable)
        try:
            inner = n_cell.find_element(By.CSS_SELECTOR, "div[title]")
            name = inner.get_attribute("title").strip().lower()
        except Exception:
            name = n_cell.text.strip().lower()

        if symbol and name:
            pairs.append((symbol, name))

    return pairs


def main():
    driver = build_driver(headless=True)
    data = defaultdict(list)

    BASE_URL = (
        "https://finance.yahoo.com/research-hub/screener/equity/?start={}&count=100"
    )

    # Warm-up: let Yahoo set cookies / fire consent once
    print("=== Warming up on Yahoo Finance ===")
    driver.get("https://finance.yahoo.com/research-hub/screener/equity/?start={}&count=100")
    time.sleep(4)
    dismiss_overlays(driver)

    try:
        for start in range(0, 10000, 100):
            url = BASE_URL.format(start)
            print(f"\nFetching page start={start}: {url}")
            driver.get(url)
            time.sleep(3)
            dismiss_overlays(driver)

            rows = wait_for_rows(driver)
            if not rows:
                print(f"  No rows after timeout — skipping start={start}")
                continue

            pairs = parse_page(driver)
            if not pairs:
                print(f"  Parsed 0 pairs — skipping start={start}")
                continue

            for symbol, name in pairs:
                first_word = name.split()[0]
                data[first_word].append([name, symbol])

            total_so_far = sum(len(v) for v in data.values())
            print(f"  Processed {len(pairs)} entries  (total so far: {total_so_far})")
            time.sleep(2)  # polite delay

    finally:
        driver.quit()
        print("\nBrowser closed.")

    with open("ticker_map.json", "w") as f:
        json.dump(data, f, indent=2)

    total = sum(len(v) for v in data.values())
    print(f"\nSaved ticker_map.json — {total} tickers in {len(data)} groups.")


if __name__ == "__main__":
    main()