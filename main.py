from flask import Flask, request
import datetime
import requests
import os

app = Flask(__name__)
session = requests.Session()
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- GLOBAL SESSION TOKENS ---
auth_headers = {}

# --- FOREX.COM LOGIN ---
def login_to_forex():
    global auth_headers
    url = "https://ciapi.cityindex.com/TradingAPI/session"
    payload = {
        "UserName": os.getenv("FOREX_EMAIL"),
        "Password": os.getenv("FOREX_PASSWORD"),
        "AppKey": "3c5ddbf9ff634a0b86f07a5c132b048b"
    }

    response = session.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("✅ Logged in to FOREX.com API")
        cst = response.headers.get("CST")
        xst = response.headers.get("X-SECURITY-TOKEN")
        auth_headers = {
            **headers,
            "CST": cst,
            "X-SECURITY-TOKEN": xst
        }
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)

# --- FETCH TRADING ACCOUNT ID ---
def get_trading_account_id():
    url = "https://ciapi.cityindex.com/TradingAPI/useraccount/"  # Gets all user accounts
    response = session.get(url, headers=auth_headers)

    if response.status_code == 200:
        accounts = response.json().get("TradingAccounts", [])
        return accounts[0]["TradingAccountId"] if accounts else None
    else:
        print("❌ Failed to retrieve Trading Account ID")
        print(response.text)
        return None

# --- PLACE ORDER FUNCTION ---
def place_order(order_type):
    url = "https://ciapi.cityindex.com/TradingAPI/order/newtradeorder"
    account_id = get_trading_account_id()

    if not account_id:
        print("❌ Cannot place order without a valid account ID")
        return

    payload = {
        "MarketId": 401484347,
        "Direction": "buy" if order_type.upper() == "BUY" else "sell",
        "Quantity": 1000,
        "OrderType": "market",
        "TradingAccountId": account_id,
        "AuditId": "webhook",
        "MarketName": "EUR/USD"
    }

    response = session.post(url, json=payload, headers=auth_headers)

    if response.status_code == 401:
        print("🔁 Session expired. Re-logging in...")
        login_to_forex()
        account_id = get_trading_account_id()
        payload["TradingAccountId"] = account_id
        response = session.post(url, json=payload, headers=auth_headers)

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
