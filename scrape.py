import requests
from bs4 import BeautifulSoup
import re

URL = 'https://tradelinesupply.com/pricing/'

def scrape_and_group_by_price():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')

    buckets = {
        '0-150': [],
        '151-300': [],
        '301-500': [],
        '501+': []
    }

    for row in rows:
        try:
            product_td = row.find('td', class_='product_data')
            price_td = row.find('td', class_='product_price')

            if not product_td or not price_td:
                continue

            bank_name = product_td.get('data-bankname', '').strip()
            credit_limit_raw = product_td.get('data-creditlimit', '').strip().replace('$', '').replace(',', '')
            credit_limit = int(credit_limit_raw) if credit_limit_raw.isdigit() else 0
            date_opened = product_td.get('data-dateopened', '').strip()
            purchase_by = product_td.get('data-purchasebydate', '').strip()
            reporting_period = product_td.get('data-reportingperiod', '').strip()
            availability = product_td.get('data-availability', '').strip()

            price_text = price_td.get_text(strip=True)
            price_match = re.search(r"\$\s?(\d+(?:,\d{3})*(?:\.\d{2})?)", price_text)
            if not price_match:
                continue
            base_price = float(price_match.group(1).replace(",", ""))
            final_price = base_price + 100

            formatted = (
                f"Bank: {bank_name}\n"
                f"Credit Limit: ${credit_limit:,}\n"
                f"Date Opened: {date_opened}\n"
                f"Purchase Deadline: {purchase_by}\n"
                f"Reporting Period: {reporting_period}\n"
                f"Availability: {availability}\n"
                f"Price: ${final_price:,.2f}"
            )

            item = {
                'bank': bank_name,
                'text': formatted,
                'price': final_price,
                'limit': credit_limit
            }

            if final_price <= 150:
                buckets['0-150'].append(item)
            elif final_price <= 300:
                buckets['151-300'].append(item)
            elif final_price <= 500:
                buckets['301-500'].append(item)
            else:
                buckets['501+'].append(item)

        except Exception:
            continue

    for key in buckets:
        buckets[key] = sorted(buckets[key], key=lambda x: x['price'])

    return buckets
