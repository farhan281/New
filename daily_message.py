import requests
import schedule
import time
from datetime import datetime

# List of Discord webhook URLs
webhook_urls = [
    'https://discord.com/api/webhooks/1379367634675433574/pVA9b1TdBomQewJO0PVEPXexgWA-IfaQbDJPbTmWsKKQgkC2Ljx8sGjEsiXUiKhpQwoT',
    'https://discord.com/api/webhooks/1379388709832626206/k7CoIYRcdu1TOfccCjnD5T-ol75qPaNJhlq0aLLNi10IUDRCxgK6jgzgu5S_o81fjSZ_',
    'https://discord.com/api/webhooks/1379391408867377265/9v9E6_6EyRPTx9P4CyocWDn_Fk9xb0aP9AsRbJS0jaYN7ZYOuVKpTaMH3KWb8d0YaUbh'
]

def send_discord_message():
    today = datetime.today().weekday()  # Monday = 0, Sunday = 6
    if today in (5, 6):  # Skip Saturday and Sunday
        print("Weekend detected. Skipping message.")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "content": "🕌 ASAR Salaah at 5:30 PM, In shaa Allah",
        "username": "SalaahTimeBot"
    }

    for url in webhook_urls:
        try:
            response = requests.post(url, json=data)
            if response.status_code == 204:
                print(f"Message sent successfully to {url}")
            else:
                print(f"Failed to send message to {url}. Status: {response.status_code}")
        except Exception as e:
            print(f"Error sending message to {url}: {e}")

# Schedule message at 17:15 (5:15 PM) every weekday
schedule.every().day.at("17:15").do(send_discord_message)

print("Scheduler started. Will send message at 17:15 PM (Mon–Fri)...")

while True:
    schedule.run_pending()
    time.sleep(5)
