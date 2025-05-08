from flask import Flask, request
import datetime
import requests
import os

app = Flask(__name__)
session = requests.Session()

# Store account ID after login
account_id = None

# --- LOGIN ---
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
        # Now fetch trading account ID
        acct_resp = session.get("https://ciapi.cityindex.com/TradingAPI/useraccount")
        if acct_resp.status_code == 200:
            accounts = acct_resp.json().get("TradingAccounts", [])
            if accounts:
                account_id = accounts[0]["TradingAccountId"]
                print(f"✅ Retrieved Trading Account ID: {account_id}")
            else:
                print("❌ No trading accounts found.")
        else:
            print("❌ Failed to retrieve Trading Account ID")
            print(acct_resp.text)
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)

# --- PLACE ORDER ---
def place_order(order_type):
    global account_id
    if not account_id:
        print("❌ Cannot place order: account ID missing")
        return

    url = "https://ciapi.cityindex.com/TradingAPI/order/newtradeorder"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "MarketId": 401484347,
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

# --- WEBHOOK ---
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

# --- STARTUP ---
login_to_forex()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
