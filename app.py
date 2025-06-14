from flask import Flask, request, redirect, Response
from scrape import scrape_and_group_by_price
import stripe
import math

app = Flask(__name__)
stripe.api_key = "pk_live_51QktmBKIz3f1Y2XMgQRdYnFUSaw4V8m3RLuNRh8ZzRblq5yLY06AU2MjINw1pjYGQieud9TNrilmzHxfYIWuW3on00uzEjow9H"

price_buckets = {
    '0-150': (0, 150),
    '151-300': (151, 300),
    '301-500': (301, 500),
    '501+': (501, float('inf'))
}

@app.route('/')
def select_price_range():
    html = "<h1>Select a Price Range</h1><ul>"
    for label in price_buckets:
        html += f"<li><a href='/banks?range={label}'>{label.replace('-', '–')}</a></li>"
    html += "</ul>"
    return html

@app.route('/banks')
def select_bank():
    selected_range = request.args.get('range')
    if selected_range not in price_buckets:
        return "Invalid range", 400

    buckets = scrape_and_group_by_price()
    items = buckets.get(selected_range, [])
    banks = sorted(set(item['bank'] for item in items))

    html = f"<h1>Choose a Bank for Price Range {selected_range.replace('-', '–')}</h1><ul>"
    for bank in banks:
        html += f"<li><a href='/tradelines?range={selected_range}&bank={bank}'>{bank}</a></li>"
    html += "</ul><a href='/'>⬅ Back</a>"
    return html

@app.route('/tradelines')
def show_tradelines():
    selected_range = request.args.get('range')
    bank = request.args.get('bank')
    page = int(request.args.get('page', 1))

    if selected_range not in price_buckets or not bank:
        return "Invalid request", 400

    buckets = scrape_and_group_by_price()
    all_items = [item for item in buckets.get(selected_range, []) if item['bank'] == bank]
    total_pages = max(1, math.ceil(len(all_items) / 20))
    page = min(max(page, 1), total_pages)
    start = (page - 1) * 20
    end = start + 20
    items = all_items[start:end]

    html = f"<h1>{bank} Tradelines in {selected_range.replace('-', '–')}</h1><div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;'>"

    for item in items:
        html += "<div style='border:1px solid #ccc;padding:15px;border-radius:10px;background:#fff;'>"
        html += f"<h3>{item['bank']}</h3>"
        for line in item['text'].split('\n'):
            if "Price" in line:
                html += f"<p style='color:#27ae60;font-weight:bold;'>{line}</p>"
            else:
                html += f"<p>{line}</p>"
        html += f"<a href='/buy?bank={item['bank']}&price={item['price']:.2f}' target='_blank'>Buy Now</a>"
        html += "</div>"

    html += "</div><br><div>"

    if page > 1:
        html += f"<a href='/tradelines?range={selected_range}&bank={bank}&page={page - 1}'>⬅ Prev</a> "

    if page < total_pages:
        html += f"<a href='/tradelines?range={selected_range}&bank={bank}&page={page + 1}'>Next ➡</a>"

    html += "</div><br><a href='/banks?range={0}'>⬅ Back to Banks</a>".format(selected_range)
    return html

@app.route('/buy')
def buy():
    bank = request.args.get("bank")
    price = float(request.args.get("price", 0))

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"Tradeline - {bank}",
                    },
                    'unit_amount': int(price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return f"Error: {str(e)}", 500
