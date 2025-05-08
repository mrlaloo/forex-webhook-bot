from flask import Flask, request
import requests
import os
import datetime

app = Flask(__name__)
session = requests.Session()

# --- GLOBAL HEADERS FOR API CALLS ---
BASE_URL = "https://ciapi.cityindex.com/TradingAPI"

# --- LOGIN FUNCTION ---
def login_to_forex():
    url = f"{BASE_URL}/session"
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
        # Store session headers for CST and security token
        session.headers.update({
            "CST": response.headers.get("CST", ""),
            "X-SECURITY-TOKEN": response.headers.get("X-SECURITY-TOKEN", "")
        })
        return True
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return False

# --- GET ACCOUNT ID ---
def get_account_id():
    url = f"{BASE_URL}/useraccount"
    response = session.get(url)

    if response.status_code == 200:
        accounts = response.json().get("TradingAccounts", [])
        if accounts:
            return accounts[0]["TradingAccountId"]
        else:
            print("⚠️ No trading accounts found.")
            return None
    else:
        print("❌ Failed to retrieve Trading Account ID")
        print(response.text)
        return None

# --- PLACE ORDER FUNCTION ---
def place_order(order_type):
    if not login_to_forex():
        return

    account_id = get_account_id()
    if not account_id:
        print("❌ Cannot place order without a valid account ID")
        return

    url = f"{BASE_URL}/order/newtradeorder"
    payload = {
        "MarketId": 401484347,  # EUR/USD
        "Direction": "buy" if order_type == "BUY" else "sell",
        "Quantity": 1000,  # Forex minimum
        "OrderType": "market",
        "TradingAccountId": account_id,
        "AuditId": "webhook",
        "MarketName": "EUR/USD"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

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
    message = data.get("message", "")
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] 🔔 TradingView Alert Received: {message}")

    if "BUY EURUSD" in message.upper():
        place_order("BUY")
    elif "SELL EURUSD" in message.upper():
        place_order("SELL")
    else:
        print("⚠️ Unrecognized message format")

    return {"status": "ok"}, 200

# --- STARTUP ---
if __name__ == '__main__':
    login_to_forex()
    app.run(host='0.0.0.0', port=8080)
