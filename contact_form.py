import time
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    InvalidElementStateException,
    TimeoutException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------
# 1) Your contact details + message
# -----------------------------
contact_info = {
    "first_name": "Rafiq",
    "last_name": "Ansari",
    "full_name": "Rafiq Ansari",  # fallback if separate first/last not found
    "email": "rafiq@perceptionsystem.net",
    "phone": "14085209495",
    "company": "Perception System",
    "website": "https://www.perceptionsystem.com",
    "subject": "Work Now, Pay Later model—to help you scale risk-free",
    "budget": "0",
    "address": "Ahmedabad Gujrat India",
    "message": """Hi there,

I’d like to connect and share how Perception Systems helps businesses scale efficiently with:

✅ Tailored tech solutions: Web/mobile apps, POS systems, recruitment software.
✅ Digital marketing: SEO, SMM, Paid Ads.
✅ FREE CRM + pay only after results
✅ Trusted by Dubai Gov, Stanford Uni & more

Let’s discuss streamlining ops or boosting growth!"""
}

# -----------------------------
# 2) URLs to process
# -----------------------------
urls = [
   

"http://www.b-meson.com.ng/contact",
"http://www.baardandpartners.co.za/",
"http://www.backpackerjobboard.com.au/contact/",
"http://www.baforhire.com/contact"

]

# -----------------------------
# 3) Helper functions for field‐filling
# -----------------------------
def try_fill_input_element(driver, elem, value):
    """
    Scrolls the element into view, removes any readonly/disabled attributes,
    then tries to clear() and send_keys(value). Returns True if successful.
    """
    try:
        # Scroll element into view
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", elem
        )
        # Remove readonly/disabled if present
        driver.execute_script(
            "arguments[0].removeAttribute('readonly'); arguments[0].removeAttribute('disabled');",
            elem
        )
        elem.clear()
        elem.send_keys(value)
        return True
    except (ElementNotInteractableException, InvalidElementStateException):
        return False

def fill_field_by_keywords(driver, keywords, value, tag="input"):
    """
    Searches for an <input> (or <textarea>) whose name, id, or placeholder 
    contains any of the given keywords (case-insensitive). If found, attempts 
    scrollIntoView + remove readonly/disabled + clear() + send_keys(value). 
    Returns True if typing succeeded, False otherwise.
    """
    xpath_checks = []
    for kw in keywords:
        kw_lower = kw.lower()
        xpath_checks.append(
            f"contains(translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{kw_lower}')"
        )
        xpath_checks.append(
            f"contains(translate(@id,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{kw_lower}')"
        )
        xpath_checks.append(
            f"contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{kw_lower}')"
        )
    if tag.lower() == "textarea":
        xpath = f"//textarea[{ ' or '.join(xpath_checks) }]"
    else:
        xpath = f"//input[{ ' or '.join(xpath_checks) }]"
    try:
        elem = driver.find_element(By.XPATH, xpath)
        return try_fill_input_element(driver, elem, value)
    except NoSuchElementException:
        return False

def click_submit_button(driver):
    """
    Finds any <button> or <input type='submit|button'> whose text/value 
    matches common submit/send/contact patterns. Scrolls into view and clicks it.
    Returns True if clicked, False otherwise.
    """
    submit_patterns = [
        r"submit", r"send", r"contact", r"enquire", r"inquire",
        r"get\s*in\s*touch", r"request", r"book", r"apply"
    ]

    # 1) Look through <button> elements by visible text
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        text = btn.text.strip().lower()
        for pat in submit_patterns:
            if re.search(pat, text):
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    btn.click()
                    return True
                except Exception:
                    pass

    # 2) Look through <input type='submit' or type='button'> by value attribute
    inputs = driver.find_elements(By.XPATH, "//input[@type='submit' or @type='button']")
    for inp in inputs:
        val = (inp.get_attribute("value") or "").strip().lower()
        if any(re.search(pat, val) for pat in submit_patterns):
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inp)
                inp.click()
                return True
            except Exception:
                pass

    return False

# -----------------------------
# 4) Main routine: open each URL in a new tab, attempt autofill + manual fallback
# -----------------------------
def main():
    global driver
    options = webdriver.ChromeOptions()
    # If you prefer headless mode (no browser window), uncomment the next line:
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    # Prepare results list
    results = []

    # Open a blank initial tab
    driver.get("about:blank")

    for url in urls:
        print(f"\n→ Opening tab for: {url}")

        # 1) Open a new blank tab and switch to it
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])

        # Initialize a result dict for this URL
        result = {
            "url": url,
            "first_name_filled": False,
            "last_name_filled": False,
            "full_name_filled": False,
            "email_filled": False,
            "phone_filled": False,
            "company_filled": False,
            "org_filled": False,
            "website_filled": False,
            "subject_filled": False,
            "budget_filled": False,
            "address_filled": False,
            "message_filled": False,
            "submitted": False,
            "manual_confirmation": False
        }

        # 2) Navigate to the contact page
        try:
            driver.get(url)
        except Exception as e:
            print(f"  [!] Could not load page: {e}")
            # Leave this tab open for manual fill
            results.append(result)
            continue

        # 3) Wait up to 10 seconds for at least one <input> to appear
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "input"))
            )
        except TimeoutException:
            print("  [!] No form inputs detected after waiting. Leaving tab open for manual fill.")
            results.append(result)
            continue

        time.sleep(1)  # allow JS-rendered fields to appear

        # 4) Attempt to fill fields

        # 4.1) First/Last Name or Full Name fallback
        first_keywords = [
            "first", "firstname", "first_name", "fname",
            "givenname", "given_name", "first-name",
            "contact_first", "user_first"
        ]
        last_keywords = [
            "last", "lastname", "last_name", "lname",
            "surname", "familyname", "family_name",
            "last-name", "contact_last", "user_last"
        ]
        full_keywords = [
            "name", "fullname", "full_name", "yourname",
            "your_name", "contact_name", "your_fullname"
        ]
        did_first = fill_field_by_keywords(driver, first_keywords, contact_info["first_name"])
        did_last  = fill_field_by_keywords(driver, last_keywords, contact_info["last_name"])
        if did_first and did_last:
            print("   • First & Last name filled separately")
            result["first_name_filled"] = True
            result["last_name_filled"] = True
        else:
            if not (did_first or did_last):
                did_full = fill_field_by_keywords(driver, full_keywords, contact_info["full_name"])
                if did_full:
                    print("   • Used generic 'Name' field for full name")
                    result["full_name_filled"] = True
                else:
                    print("   • Name fields NOT found or not interactable")
            else:
                if did_first:
                    result["first_name_filled"] = True
                if did_last:
                    result["last_name_filled"] = True
                if not did_first:
                    print("   • First name NOT found or not interactable, but last name was filled")
                if not did_last:
                    print("   • Last name NOT found or not interactable, but first name was filled")

        # 4.2) Email
        try:
            email_input = driver.find_element(By.XPATH, "//input[@type='email']")
            if try_fill_input_element(driver, email_input, contact_info["email"]):
                print("   • Email filled (type='email')")
                result["email_filled"] = True
            else:
                print("   • Found <input type='email'> but could not type into it")
        except NoSuchElementException:
            email_keywords = [
                "email", "e-mail", "email_address", "emailaddress",
                "your_email", "youremail", "contact_email", "user_email"
            ]
            did_email = fill_field_by_keywords(driver, email_keywords, contact_info["email"])
            if did_email:
                print("   • Email filled (by keyword)")
                result["email_filled"] = True
            else:
                print("   • Email NOT found or not interactable")

        # 4.3) Phone
        phone_keywords = [
            "phone", "telephone", "tel", "mobile", "mobile_number",
            "phone_number", "phonenumber", "your_phone", "yourphone",
            "your_mobile", "contact_phone", "phone_code", "country_code",
            "tel_code"
        ]
        did_phone = fill_field_by_keywords(driver, phone_keywords, contact_info["phone"])
        if did_phone:
            print("   • Phone filled")
            result["phone_filled"] = True
        else:
            print("   • Phone NOT found or not interactable")

        # 4.4) Company / Org fallback
        company_keywords = [
            "company", "company_name", "companyname",
            "business", "business_name", "firm", "agency"
        ]
        org_keywords = [
            "organization", "organisation", "org", "org_name", "employer"
        ]
        did_company = fill_field_by_keywords(driver, company_keywords, contact_info["company"])
        if did_company:
            print("   • Company filled")
            result["company_filled"] = True
        else:
            did_org = fill_field_by_keywords(driver, org_keywords, contact_info["company"])
            if did_org:
                print("   • Organization/Org filled (fallback)")
                result["org_filled"] = True
            else:
                print("   • Company/Organization NOT found or not interactable")

        # 4.5) Website / URL
        website_keywords = [
            "website", "website_url", "url", "web",
            "websiteaddress", "homepage", "link"
        ]
        did_website = fill_field_by_keywords(driver, website_keywords, contact_info["website"])
        if did_website:
            print("   • Website filled")
            result["website_filled"] = True
        else:
            print("   • Website NOT found or not interactable")

        # 4.6) Subject / Inquiry
        subject_keywords = [
            "subject", "inquiry", "enquiry", "inquiry_type",
            "reason", "topic", "message_subject"
        ]
        did_subject = fill_field_by_keywords(driver, subject_keywords, contact_info["subject"])
        if did_subject:
            print("   • Subject/Inquiry filled")
            result["subject_filled"] = True
        else:
            print("   • Subject/Inquiry NOT found or not interactable")

        # 4.7) Budget / Project Details
        budget_keywords = [
            "budget", "project", "project_details",
            "project_description", "project_scope", "budget_estimate",
            "cost", "estimated_budget", "fee"
        ]
        did_budget = fill_field_by_keywords(driver, budget_keywords, contact_info["budget"])
        if did_budget:
            print("   • Budget/Project filled")
            result["budget_filled"] = True
        else:
            print("   • Budget/Project NOT found or not interactable")

        # 4.8) Address / Location
        address_keywords = [
            "address", "location", "city", "state",
            "province", "country", "postal_code", "zip_code",
            "postcode", "street", "street_address"
        ]
        did_address = fill_field_by_keywords(driver, address_keywords, contact_info["address"])
        if did_address:
            print("   • Address/Location filled")
            result["address_filled"] = True
        else:
            print("   • Address/Location NOT found or not interactable")

        # 4.9) Message / Comments (first try <textarea>)
        try:
            textarea = driver.find_element(By.TAG_NAME, "textarea")
            if try_fill_input_element(driver, textarea, contact_info["message"]):
                print("   • Message filled (textarea)")
                result["message_filled"] = True
            else:
                print("   • Found <textarea> but could not type into it")
        except NoSuchElementException:
            message_keywords = [
                "message", "comments", "comment", "description",
                "details", "enquiry", "inquiry", "notes",
                "additional_info", "your_message"
            ]
            did_msg = fill_field_by_keywords(driver, message_keywords, contact_info["message"], tag="input")
            if did_msg:
                print("   • Message filled (input fallback)")
                result["message_filled"] = True
            else:
                print("   • Message NOT found or not interactable")

        # 5) Attempt to click a Submit/Send/Contact button
        submitted = click_submit_button(driver)
        if submitted:
            print("   → Form submitted automatically. The tab will remain open for your review.")
            result["submitted"] = True
            results.append(result)

            # Do NOT close the tab. Move on to the next URL.
            # Switch back to the original blank tab, then continue.
            driver.switch_to.window(driver.window_handles[0])
        else:
            print("   → Automated submission failed. You can fill this form manually.")
            # Leave this tab open, prompt user to fill manually:
            input("     ⏳  Fill out (and submit) the form manually, then press ENTER here to continue...")
            print("     → Checking if the form is gone/submitted...")

            # Poll until the page no longer has any <input> elements
            while True:
                time.sleep(2)
                try:
                    driver.find_element(By.TAG_NAME, "input")
                    print("       • Form still detected. If you've submitted, please wait a moment or try again.")
                except NoSuchElementException:
                    # No <input> found—assume form is gone/submitted
                    print("       ✔️  Looks like the form is gone/submitted.")
                    result["submitted"] = True
                    result["manual_confirmation"] = True
                    break

            results.append(result)
            # Switch focus back to the blank first tab for consistency
            driver.switch_to.window(driver.window_handles[0])

        # Short pause before moving on
        time.sleep(1)

    # After processing all URLs, ensure focus is on the first (blank) tab
    driver.switch_to.window(driver.window_handles[0])

    # 6) Write results to CSV
    csv_columns = [
        "url", "first_name_filled", "last_name_filled", "full_name_filled",
        "email_filled", "phone_filled", "company_filled", "org_filled",
        "website_filled", "subject_filled", "budget_filled", "address_filled",
        "message_filled", "submitted", "manual_confirmation"
    ]
    csv_file = "contact_form_results.csv"
    try:
        with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in results:
                writer.writerow(data)
        print(f"\nResults exported to {csv_file}")
    except Exception as e:
        print(f"\n[!] Failed to write CSV: {e}")

    print("\nScript finished. All tabs remain open for your review and manual closing.")

if __name__ == "__main__":
    main()
