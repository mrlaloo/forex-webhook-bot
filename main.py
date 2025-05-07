from flask import Flask, request
import datetime
import requests
import os

app = Flask(__name__)
session = requests.Session()

# --- FOREX.COM LOGIN ---
def login_to_forex():
    url = "https://ciapi.cityindex.com/TradingAPI/session"
    payload = {
        "UserName": os.getenv("FOREX_EMAIL"),
        "Password": os.getenv("FOREX_PASSWORD"),
        "AppKey": "CIAPI.test"
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = session.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("✅ Logged in to FOREX.com API")
    else:
        print(f"❌ Login failed: {response.status_code}")
def place_order(order_type):
    account_id = os.getenv("FOREX_ACCOUNT_ID")
    url = "https://ciapi.cityindex.com/TradingAPI/order/newtradeorder"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "MarketId": 401484347,  # EUR/USD market ID (default; confirm if needed)
        "Direction": "buy" if order_type == "BUY" else "sell",
        "Quantity": 1,
        "OrderType": "market",
        "TradingAccountId": int(account_id),
        "AuditId": "webhook"
    }

    response = session.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(f"✅ {order_type} order placed successfully")
    else:
        print(f"❌ Failed to place {order_type} order: {response.status_code}")
        print(response.text)
        print(response.text)
def place_order(direction):
    url = "https://ciapi.cityindex.com/TradingAPI/order/newtrade"
    payload = {
        "MarketId": 401484347,  # EUR/USD — adjust if needed
        "Direction": "buy" if direction == "BUY" else "sell",
        "Quantity": 1,
        "OrderType": "Market",
        "TradingAccountId": int(os.getenv("FOREX_ACCOUNT_ID")),
        "MarketName": "EUR/USD"
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = session.post(url, json=payload, headers=headers)
    print(f"📤 Order response: {response.status_code}")
    print(response.text)

# --- WEBHOOK ENDPOINT ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    message = data.get('message', '')

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] 🔔 TradingView Alert Received: {message}")

    if "BUY EURUSD" in message.upper():
        place_order("BUY")

        # TODO: Send real trade request here using `session`
    elif "SELL EURUSD" in message.upper():
       place_order("SELL")

        # TODO: Send real trade request here using `session`
    else:
        print("⚠️ Unrecognized message format")

    return {'status': 'ok'}, 200

# --- START APP ---
login_to_forex()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
