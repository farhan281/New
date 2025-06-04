import time
import re
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycby_MJuufa6fKu7XSoWch4wkU7flXq0gxkzky-7c-ANu4W9gvkE5erNVkD_WrBOzW_OJkw/exec"

urls = [
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

SOCIAL_DOMAINS = {
    "LinkedIn": "linkedin.com",
    "Facebook": "facebook.com",
    "Twitter": "twitter.com",
    "Instagram": "instagram.com",
    "YouTube": "youtube.com"
}

PHONE_REGEX = re.compile(r"""(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)\d{3,4}[-.\s]?\d{3,4}""", re.VERBOSE)

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
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(10)
    driver.implicitly_wait(5)
    return driver

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

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            result["error"] = f"Error {resp.status_code}"
            return result
    except Exception:
        result["error"] = "Error 500 (request failed)"
        return result

    try:
        driver.get(url)
        page_html = driver.page_source
    except Exception as e:
        result["error"] = f"Selenium timeout: {str(e)}"
        return result

    soup = BeautifulSoup(page_html, "html.parser")
    text = soup.get_text(separator="\n")

    emails = set(re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+", text))
    phones = set(m.strip() for m in re.findall(PHONE_REGEX, text))

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
            contact_html = driver.page_source
            contact_soup = BeautifulSoup(contact_html, "html.parser")
            contact_text = contact_soup.get_text(separator="\n")
            more_emails = set(re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+", contact_text))
            more_phones = set(m.strip() for m in re.findall(PHONE_REGEX, contact_text))
            emails |= more_emails
            phones |= more_phones
        except Exception:
            pass

    current_soup = contact_soup if contact_soup else soup

    for a in current_soup.find_all("a", href=True):
        href_full = urljoin(url, a["href"])
        for name, domain in SOCIAL_DOMAINS.items():
            if domain in href_full and not result["social_links"][name]:
                result["social_links"][name] = href_full

    result["contact_form"] = contact_form_link
    result["emails"] = sorted(list(emails))
    result["phones"] = sorted(list(phones))

    return result

def main():
    driver = create_selenium_driver()
    all_results = []

    max_emails = 0
    max_phones = 0
    temp_results = []

    for url in urls:
        data = extract_contact_info_with_selenium(url, driver)
        temp_results.append(data)
        max_emails = max(max_emails, len(data["emails"]))
        max_phones = max(max_phones, len(data["phones"]))

    driver.quit()

    header = ["Company", "URL", "Contact Form"]
    header += [f"Email {i+1}" for i in range(max_emails)]
    header += [f"Phone {i+1}" for i in range(max_phones)]
    header += list(SOCIAL_DOMAINS.keys())
    header.append("Error")

    header_payload = {"row": header, "isHeader": True}
    try:
        resp = requests.post(WEBHOOK_URL, json=header_payload, timeout=30)
        print("Sent header to sheet:", resp.text)
    except Exception as ex:
        print("Error sending header:", ex)
        return

    driver = create_selenium_driver()
    for data in tqdm(temp_results, desc="Posting rows to sheet"):
        row = [
            data["company_name"],
            data["url"],
            data["contact_form"]
        ]
        for i in range(max_emails):
            row.append(data["emails"][i] if i < len(data["emails"]) else "")
        for i in range(max_phones):
            row.append(data["phones"][i] if i < len(data["phones"]) else "")
        for name in SOCIAL_DOMAINS:
            row.append(data["social_links"][name])
        row.append(data["error"])

        try:
            requests.post(WEBHOOK_URL, json={"row": row}, timeout=30)
        except Exception as ex:
            print(f"Error posting row for {data['url']}: {ex}")
    driver.quit()

if __name__ == "__main__":
    main()
