import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SESSION = requests.Session()
BASE_URL = "https://ciapi-ci-demo.fxcorporate.com"
LOGIN_URL = f"{BASE_URL}/session"
ACCOUNTS_URL = f"{BASE_URL}/TradingAccounts"
ORDER_URL = f"{BASE_URL}/order/newtradeorder"


def login_to_forex():
    email = os.getenv("FOREX_EMAIL")
    password = os.getenv("FOREX_PASSWORD")
    
    payload = {
        "UserName": email,
        "Password": password,
        "AppKey": "WebAPI"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = SESSION.post(LOGIN_URL, json=payload, headers=headers)

    if response.status_code == 200:
        print("✅ Logged in to FOREX.com API")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)


def get_trading_account_id():
    response = SESSION.get(ACCOUNTS_URL)

    if response.status_code == 200:
        accounts = response.json()["TradingAccounts"]
        if accounts:
            return accounts[0]["TradingAccountId"]
        else:
            print("⚠️ No trading accounts found.")
    else:
        print("❌ Failed to retrieve Trading Account ID")
        print(response.text)
    return None


def place_order(order_type):
    account_id = get_trading_account_id()
    if not account_id:
        print("❌ Cannot place order without a valid account ID")
        return

    payload = {
        "MarketId": 401484347,  # EUR/USD
        "Direction": "buy" if order_type == "BUY" else "sell",
        "Quantity": 1000,
        "OrderType": "market",
        "TradingAccountId": account_id,
        "AuditId": "webhook",
        "MarketName": "EUR/USD"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = SESSION.post(ORDER_URL, json=payload, headers=headers)

    if response.status_code == 401:
        print("🔒 Session expired. Re-logging in...")
        login_to_forex()
        response = SESSION.post(ORDER_URL, json=payload, headers=headers)

    if response.status_code == 200:
        print("✅ Order placed successfully!")
    else:
        print(f"❌ Failed to place {order_type} order: {response.status_code}")
        print(response.text)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"🚨 TradingView Alert Received: {data.get('ticker')}")

    order_type = data.get("order", "").upper()
    if order_type in ["BUY", "SELL"]:
        place_order(order_type)
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Invalid order type"}), 400


if __name__ == "__main__":
    login_to_forex()
    app.run(host="0.0.0.0", port=10000)
