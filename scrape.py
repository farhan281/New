import time
import re
import csv
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

# ────────────────────────────────────────────────────────────────────
# 1) Paste your deployed Apps Script webhook URL here
# ────────────────────────────────────────────────────────────────────
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxvHc74uyZ03QLoR3KuCNf3-inhn3zitmq2Z8vxsM3WTaUOIYtD8QBvTvnJI8TXkza6Vg/exec"

# List of company contact page URLs to scrape (adjust as needed)
urls = [
    "http://www.aire-search.com/#contact",
    "http://www.airexecsearch.com/contact-us",
    # … (other URLs) …
]

# Domains to recognize social media links
SOCIAL_DOMAINS = {
    "LinkedIn":  "linkedin.com",
    "Facebook":  "facebook.com",
    "Twitter":   "twitter.com",
    "Instagram": "instagram.com",
    "YouTube":   "youtube.com"
}

# Regular expression to match phone numbers (with optional country/area codes)
PHONE_REGEX = re.compile(r"""
  (?:\+?\d{1,3}[-.\s]?)?        # optional country code
  (?:\(?\d{2,4}\)?[-.\s]?)      # optional area code
  \d{3,4}[-.\s]?\d{3,4}         # main number
  """, re.VERBOSE)

def get_company_name(url: str) -> str:
    """Extract a simple company name from the URL."""
    domain = urlparse(url).netloc
    base = domain.replace("www.", "").split(".")[0]
    return base.capitalize()

def create_selenium_driver() -> webdriver.Chrome:
    """Initialize a headless Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")
    service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_contact_info_with_selenium(url: str, driver: webdriver.Chrome) -> dict:
    """
    Scrape a single URL for contact details:
      - HTTP status
      - Contact form link
      - Email addresses
      - Phone numbers
      - Social media links
    Returns a dict with all findings or an error string.
    """
    result = {
        "company_name": get_company_name(url),
        "url": url,
        "contact_form": "",
        "emails": [],
        "phones": [],
        "social_links": {k: "" for k in SOCIAL_DOMAINS},
        "error": ""
    }

    # 1) Check HTTP status via requests
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        result["error"] = "Error 500 (request failed)"
        return result

    if resp.status_code != 200:
        result["error"] = f"Error {resp.status_code}"
        return result

    # 2) Load the page in Selenium and get HTML
    try:
        driver.get(url)
        time.sleep(3)
        page_html = driver.page_source
    except Exception:
        result["error"] = "Error 500 (selenium failed)"
        return result

    soup = BeautifulSoup(page_html, "html.parser")
    text = soup.get_text(separator="\n")

    # Extract emails and phones from the page text
    emails = set(re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+", text))
    phones = set(m.strip() for m in re.findall(PHONE_REGEX, text))

    # Find the first “Contact” link
    contact_form_link = ""
    for a in soup.find_all("a", href=True):
        href_text = a.get_text().strip().lower()
        href_url = a["href"].strip().lower()
        if "contact" in href_text or "contact" in href_url:
            contact_form_link = urljoin(url, a["href"])
            break

    # If a contact page was found, re-scrape it for more info
    contact_soup = None
    if contact_form_link:
        try:
            driver.get(contact_form_link)
            time.sleep(2)
            contact_html = driver.page_source
            contact_soup = BeautifulSoup(contact_html, "html.parser")
            contact_text = contact_soup.get_text(separator="\n")
            emails |= set(re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+", contact_text))
            phones |= set(m.strip() for m in re.findall(PHONE_REGEX, contact_text))
        except Exception:
            pass

    # Choose which soup to use for social links
    current_soup = contact_soup if contact_soup else soup

    # Extract social media links
    social_links = {k: "" for k in SOCIAL_DOMAINS}
    for a in current_soup.find_all("a", href=True):
        href_full = urljoin(url, a["href"])
        for name, domain in SOCIAL_DOMAINS.items():
            if domain in href_full and not social_links[name]:
                social_links[name] = href_full

    # Populate result fields
    result["contact_form"] = contact_form_link
    result["emails"] = sorted(emails)
    result["phones"] = sorted(phones)
    result["social_links"] = social_links

    return result

def main():
    """Main entry point: scrape all URLs, write to CSV/JSON, then post CSV to Google Sheets."""
    driver = create_selenium_driver()
    all_results = []
    max_emails = max_phones = 0

    # Scrape each URL with progress bar
    for url in tqdm(urls, desc="Scraping URLs"):
        data = extract_contact_info_with_selenium(url, driver)
        all_results.append(data)
        max_emails = max(max_emails, len(data["emails"]))
        max_phones = max(max_phones, len(data["phones"]))

    driver.quit()

    # 1) Write detailed CSV
    csv_filename = "company_contacts_detailed.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Build header dynamically based on max counts
        header = ["Company", "URL", "Contact Form"]
        header += [f"Email {i+1}" for i in range(max_emails)]
        header += [f"Phone {i+1}" for i in range(max_phones)]
        header += list(SOCIAL_DOMAINS.keys())
        header.append("Error")
        writer.writerow(header)

        # Write each result row, padding missing values
        for item in all_results:
            row = [
                item["company_name"],
                item["url"],
                item["contact_form"]
            ]
            row += item["emails"] + [""]*(max_emails - len(item["emails"]))
            row += item["phones"] + [""]*(max_phones - len(item["phones"]))
            row += [item["social_links"].get(name, "") for name in SOCIAL_DOMAINS]
            row.append(item.get("error", ""))
            writer.writerow(row)

    print(f"✅ CSV written to {csv_filename}")

    # 2) Optionally write JSON
    json_filename = "company_contacts_detailed.json"
    with open(json_filename, "w", encoding="utf-8") as jsonfile:
        json.dump(all_results, jsonfile, indent=2, ensure_ascii=False)
    print(f"✅ JSON written to {json_filename}")

    # 3) Send full CSV text to Google Sheets via webhook
    with open(csv_filename, "r", encoding="utf-8") as f:
        csv_text = f.read()

    payload = {"csv": csv_text}
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        if resp.status_code == 200:
            print("✅ CSV successfully imported to Google Sheet:", resp.text)
        else:
            print(f"❌ Google Sheet POST failed (HTTP {resp.status_code}):", resp.text)
    except Exception as ex:
        print("❌ Exception while posting CSV to Google Sheet:", ex)

if __name__ == "__main__":
    main()
