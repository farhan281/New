# New
Python_Script_for_Data_Scraping
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
# 1) अपना Webhook URL यहां पेस्ट करें (जो आपने Apps Script डिप्लॉय करते समय कॉपी किया था)
# ────────────────────────────────────────────────────────────────────
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxvHc74uyZ03QLoR3KuCNf3-inhn3zitmq2Z8vxsM3WTaUOIYtD8QBvTvnJI8TXkza6Vg/exec"
# ────────────────────────────────────────────────────────────────────

# List of company URLs to scrape (आप अपनी लिस्ट यहां एडजस्ट कर सकते हैं)
urls = [
   "http://www.aire-search.com/#contact",
"http://www.airexecsearch.com/contact-us",
"http://www.aiselecta.com/#contact",
"http://www.ajbconsultancy.com.au/#contact",
"http://www.akashicstudiesaustralia.com/contact",
"http://www.alascogroup.com/contact",
"http://www.albany-appointments.co.uk/contact-us.html",
"http://www.alexcorreaexecutive.com.au/contact62a106c8",
"http://www.alexjamesdigital.co.uk/contact/",
"http://www.alfursanrecruitment.ae/contact-us",
"http://www.aligntalent.com.au/contact",
"http://www.alisonmanning.com/contact.html",
"http://www.alkhalidmanpower.co/contact-us",
"http://www.allaboutyouconsulting.com/html_docs/contact.html",
"http://www.allaccesstraining.co.uk/contact.php",
"http://www.allbyn.com/contact",
"http://www.allclassequipmenttraining.com/contact.html",
"http://www.allenaclarke.co.uk/index.php/contact/",
"http://www.allenjames.co.uk/contact-us",
"http://www.allskillsservices.com.au/contact-all-skills.html",
"http://www.allureconsulting.com.au/contact.html",
"http://www.almasearch.com/",
"http://www.alpaka.io/contact",
"http://www.altanarecruitment.co.uk/Contact.aspx",
"http://www.alteredresourcing.co.uk/#Contact",
]

# Domains for social links
SOCIAL_DOMAINS = {
    "LinkedIn":  "linkedin.com",
    "Facebook":  "facebook.com",
    "Twitter":   "twitter.com",
    "Instagram": "instagram.com",
    "YouTube":   "youtube.com"
}

# Phone regex
PHONE_REGEX = re.compile(r"""
  (?:\+?\d{1,3}[-.\s]?)?        # optional country code
  (?:\(?\d{2,4}\)?[-.\s]?)      # optional area code
  \d{3,4}[-.\s]?\d{3,4}         # main number
  """, re.VERBOSE)

def get_company_name(url: str) -> str:
    domain = urlparse(url).netloc
    base = domain.replace("www.", "").split(".")[0]
    return base.capitalize()

def create_selenium_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")
    service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_contact_info_with_selenium(url: str, driver: webdriver.Chrome) -> dict:
    result = {
        "company_name": get_company_name(url),
        "url": url,
        "contact_form": "",
        "emails": [],
        "phones": [],
        "social_links": {k: "" for k in SOCIAL_DOMAINS},
        "error": ""
    }

    # Step 1: HTTP status चेक
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        result["error"] = "Error 500 (request failed)"
        return result

    if resp.status_code != 200:
        result["error"] = f"Error {resp.status_code}"
        return result

    # Step 2: Selenium से पेज लोड + BeautifulSoup
    try:
        driver.get(url)
        time.sleep(3)
        page_html = driver.page_source
    except Exception:
        result["error"] = "Error 500 (selenium failed)"
        return result

    soup = BeautifulSoup(page_html, "html.parser")
    text = soup.get_text(separator="\n")

    # Extract emails & phones
    emails = set(re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+", text))
    phones = set(m.strip() for m in re.findall(PHONE_REGEX, text))

    # Find “Contact” link
    contact_form_link = ""
    for a in soup.find_all("a", href=True):
        href_text = a.get_text().strip().lower()
        href_url = a["href"].strip().lower()
        if "contact" in href_text or "contact" in href_url:
            contact_form_link = urljoin(url, a["href"])
            break

    contact_soup = None
    if contact_form_link:
        try:
            driver.get(contact_form_link)
            time.sleep(2)
            contact_html = driver.page_source
            contact_soup = BeautifulSoup(contact_html, "html.parser")
            contact_text = contact_soup.get_text(separator="\n")
            more_emails = set(re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+", contact_text))
            more_phones = set(m.strip() for m in re.findall(PHONE_REGEX, contact_text))
            emails |= more_emails
            phones |= more_phones
        except Exception:
            pass

    # कौन सा soup यूज़ करना है (contact वाला या मुख्य पेज)
    current_soup = contact_soup if contact_soup else soup

    # Social links निकालें
    social_links = {k: "" for k in SOCIAL_DOMAINS}
    for a in current_soup.find_all("a", href=True):
        href_full = urljoin(url, a["href"])
        for name, domain in SOCIAL_DOMAINS.items():
            if domain in href_full and not social_links[name]:
                social_links[name] = href_full

    result["contact_form"] = contact_form_link
    result["emails"] = sorted(list(emails))
    result["phones"] = sorted(list(phones))
    result["social_links"] = social_links

    return result

def main():
    driver = create_selenium_driver()
    all_results = []
    max_emails = 0
    max_phones = 0

    for url in tqdm(urls, desc="Scraping URLs"):
        data = extract_contact_info_with_selenium(url, driver)
        all_results.append(data)
        max_emails = max(max_emails, len(data["emails"]))
        max_phones = max(max_phones, len(data["phones"]))

    driver.quit()

    # 1) CSV लिखें
    csv_filename = "company_contacts_detailed.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        header = [
            "Company",
            "URL",
            "Contact Form"
        ]
        header += [f"Email {i+1}" for i in range(max_emails)]
        header += [f"Phone {i+1}" for i in range(max_phones)]
        header += list(SOCIAL_DOMAINS.keys())
        header.append("Error")
        writer.writerow(header)

        for item in all_results:
            row = [
                item["company_name"],
                item["url"],
                item["contact_form"]
            ]
            row += item["emails"] + [""] * (max_emails - len(item["emails"]))
            row += item["phones"] + [""] * (max_phones - len(item["phones"]))
            row += [item["social_links"].get(name, "") for name in SOCIAL_DOMAINS]
            row.append(item.get("error", ""))
            writer.writerow(row)

    print(f"✅ CSV written to {csv_filename}")

    # 2) JSON भी लिख दें (optional)
    json_filename = "company_contacts_detailed.json"
    with open(json_filename, "w", encoding="utf-8") as jsonfile:
        json.dump(all_results, jsonfile, indent=2, ensure_ascii=False)
    print(f"✅ JSON written to {json_filename}")

    # 3) अब पूरी CSV टेक्स्ट Apps Script को भेजें
    with open(csv_filename, "r", encoding="utf-8") as f:
        csv_text = f.read()

    payload = {"csv": csv_text}
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        if resp.status_code == 200:
            print("✅ Google Sheet में CSV इम्पोर्ट हो गया: ", resp.text)
        else:
            print(f"❌ Google Sheet POST failed (HTTP {resp.status_code}): {resp.text}")
    except Exception as ex:
        print("❌ Exception while posting CSV to Google Sheet:", ex)

if __name__ == "__main__":
    main()
