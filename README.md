Here’s a comprehensive `README.md` to give an overview of my toolkit, describe each script’s purpose, and guide users through installation and usage.

```markdown
# NEW [GITHUB] Automation Toolkit

A collection of scripts for scraping, data-logging, form-filling, and notifications — all tied together via Google Sheets and Discord webhooks.

---

## 📁 Repository Structure

```

NEW \[GITHUB]/
├─ contact\_form.py             # Semi-automated Selenium form autofiller
├─ daily\_message.py            # Discord webhook scheduler for Salaah reminders
├─ live-csv-to-gsheet.py       # Real-time CSV exporter + Google Sheets webhook
├─ scrape\_all\_url\_with\_s\_code.js  # Node.js crawler logging HTTP status codes
├─ scrape\_links\_to\_gsheet.py   # Python crawler that logs link statuses to Sheets
├─ scrape.py                   # Generic Python scraper for contact info (Selenium + BS4)
├─ webhook\_receiver.js         # Google Apps Script to receive POSTs and log to Sheets
└─ README.md                   # You are here

````

---

## ⚙️ Getting Started

### Requirements

- **Python 3.7+**  
- **Node.js & npm** (for the `.js` crawler)  
- **Google Apps Script** (to deploy your `webhook_receiver.js`)

#### Python Dependencies

```bash
pip install \
  requests \
  beautifulsoup4 \
  selenium \
  webdriver-manager \
  schedule \
  tqdm
````

---

## 🔌 Deploy the Google Apps Script Webhook

1. In your G Suite account, go to **Apps Script** → **New project**.
2. Paste the contents of `webhook_receiver.js`.
3. Save & **Deploy** as a **Web app** (execute as “Me”, allow “Anyone, even anonymous”).
4. Copy the **Web app URL** and update `WEBHOOK_URL` in your Python/Node scripts.

---

## 📝 Script Overviews & Usage

### 1. `contact_form.py`

Semi-automatically fills out web contact forms using Selenium, with manual fallback on failure.

```bash
python contact_form.py
```

* Opens each URL in a new tab, detects fields by keywords, attempts autofill, then either auto-submits or waits for your manual confirm.

---

### 2. `daily_message.py`

Posts a daily Asar Salaah reminder to one or more Discord channels on weekdays at 17:15.

```bash
python daily_message.py
```

* Uses `schedule` to run at 5:15 PM Mon–Fri, skips weekends.

---

### 3. `live-csv-to-gsheet.py`

Scrapes contact info for a list of URLs, writes a fixed-column CSV, and streams each row to your Google Sheet webhook in real time.

```bash
python live-csv-to-gsheet.py
```

* Adjust `MAX_EMAILS`, `MAX_PHONES`, and `urls[]` as needed.

---

### 4. `scrape_all_url_with_s_code.js`

A Node.js crawler that visits **ahmedabadbusinessdirectory.com**, logs status codes locally to `ahmedabad_links_with_status.csv`, and POSTs each result to your Apps Script webhook.

```bash
node scrape_all_url_with_s_code.js
```

* Change the `BASE_URL` and webhook URL at top of the file.

---

### 5. `scrape_links_to_gsheet.py`

Python crawler that discovers internal links, records HTTP statuses, writes to a local CSV, and mirrors results to Google Sheets.

```bash
python scrape_links_to_gsheet.py
```

* Configurable `BASE_URL` + webhook.

---

### 6. `scrape.py`

Comprehensive Selenium + BeautifulSoup scraper for detailed contact info (emails, phones, social links, contact form URL), exporting both CSV & JSON and finally pushing the CSV to Sheets.

```bash
python scrape.py
```

---

### 7. `webhook_receiver.js`

The Apps Script you deployed in “Deploy the Google Apps Script Webhook” — handles all incoming POSTs and appends rows to your active sheet.

---

## 🔄 Workflow Example

1. **Deploy** `webhook_receiver.js` in Apps Script → grab your `WEBHOOK_URL`.
2. **Configure** each script (set `WEBHOOK_URL`, target URLs, schedule times, etc.).
3. **Run** the Python/Node scripts locally (or via a cron/Task Scheduler) to:

   * Harvest data
   * Write to CSV & JSON
   * Push rows to Google Sheets in near-real time
4. **Review** your Sheet for logs, use built-in timestamps and structured columns to filter and analyze.

---

## ✨ Contributing

Feel free to open issues or PRs for:

* Adding new scraper modules
* Improving field detection in `contact_form.py`
* Supporting extra social platforms
* Enhancing error-handling, logging, or configuration

---

## 📄 License

This project is open-source; adapt and extend as you like!

