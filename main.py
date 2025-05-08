from flask import Flask, request
import datetime
import requests
import os

app = Flask(__name__)
session = requests.Session()
account_id = None  # Global variable to store TradingAccountId

# --- FOREX.COM LOGIN ---
def login_to_forex():
    global account_id
    url = "https://ciapi.cityindex.com/TradingAPI/session"
    payload = {
        "UserName": os.getenv("FOREX_EMAIL"),
        "Password": os.getenv("FOREX_PASSWORD"),
        "AppKey": "3c5ddbf9ff634a0b86f07a5c132b048b"
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = session.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("✅ Logged in to FOREX.com API")

        # Fetch account ID dynamically
        acc_response = session.get("https://ciapi.cityindex.com/TradingAPI/useraccount", headers=headers)
        if acc_response.status_code == 200:
            account_id = acc_response.json()["TradingAccounts"][0]["TradingAccountId"]
            print(f"✅ TradingAccountId fetched: {account_id}")
        else:
            print("❌ Failed to fetch TradingAccountId")
            print(acc_response.text)

    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)

# --- PLACE ORDER FUNCTION ---
def place_order(order_type):
    global account_id
    url = "https://ciapi.cityindex.com/TradingAPI/order/newtradeorder"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "MarketId": 401484347,  # EUR/USD
        "Direction": "buy" if order_type == "BUY" else "sell",
        "Quantity": 1000,
        "OrderType": "market",
        "TradingAccountId": account_id,
        "AuditId": "webhook",
        "MarketName": "EUR/USD"
    }

    response = session.post(url, json=payload, headers=headers)
    if response.status_code == 401:
        print("🔁 Session expired. Re-logging in...")
        login_to_forex()
        response = session.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(f"✅ {order_type} order placed successfully")
    else:
        print(f"❌ Failed to place {order_type} order: {response.status_code}")
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
    elif "SELL EURUSD" in message.upper():
        place_order("SELL")
    else:
        print("⚠️ Unrecognized message format")

    return {'status': 'ok'}, 200

# --- START APP ---
login_to_forex()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
