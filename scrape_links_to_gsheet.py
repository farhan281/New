import requests
from bs4 import BeautifulSoup
import csv
import time

BASE_URL = "https://www.ahmedabadbusinessdirectory.com"
VISITED = set()
FOUND_LINKS = []

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzaj5KwNO0pJKUmtGAarO-Zc7iR2nqqJFq_CMa954bRWrua6uL_pQCp0-cQoiNwRmC-/exec"

# Create or open CSV
csv_file = open("ahmedabad_links_with_status.csv", mode="w", newline='', encoding="utf-8")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Link", "Status Code"])

def log_to_gsheet(url, status_code):
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json={"url": url, "status_code": status_code})
        if response.status_code != 200:
            print(f"⚠️ GSheet Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ GSheet Exception: {e}")

def scrape_links(url):
    if url in VISITED or not url.startswith(BASE_URL):
        return
    VISITED.add(url)

    print(f"🔍 Visiting: {url}")
    try:
        response = requests.get(url, timeout=10)
        
        # Check the status code and log it
        status_code = response.status_code
        print(f"Status Code for {url}: {status_code}")

        # If status code is not 200, log and skip
        if status_code != 200:
            print(f"❌ Failed to access: {url} - Status Code: {status_code}")
            csv_writer.writerow([url, status_code])
            csv_file.flush()
            log_to_gsheet(url, status_code)
            return

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"].strip()
            if href.startswith("/"):
                full_url = BASE_URL + href
            elif href.startswith(BASE_URL):
                full_url = href
            else:
                continue  # Skip external links

            if full_url not in VISITED:
                FOUND_LINKS.append(full_url)
                csv_writer.writerow([full_url, status_code])
                csv_file.flush()
                log_to_gsheet(full_url, status_code)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error scraping {url}: {e}")

def crawl(start_url):
    scrape_links(start_url)
    index = 0
    while index < len(FOUND_LINKS):
        scrape_links(FOUND_LINKS[index])
        index += 1
        time.sleep(0.5)  # be polite to the server

if __name__ == "__main__":
    crawl(BASE_URL)
    csv_file.close()
    print("✅ Finished scraping and saving to CSV + Google Sheet.")
