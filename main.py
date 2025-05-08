import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global session and account_id
session = requests.Session()
account_id = None

def login_to_forex():
    global session, account_id
    print("🔐 Logging in to FOREX.com API")
    login_url = "https://ciapi.cityindex.com/tradingapi/session"

    payload = {
        "UserName": os.getenv("FOREX_EMAIL"),
        "Password": os.getenv("FOREX_PASSWORD"),
        "AppKey": "forex_webhook_bot"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = session.post(login_url, json=payload, headers=headers)
    if response.status_code == 200:
        print("✅ Logged in to FOREX.com API")
        # Get trading accounts
        acc_response = session.get("https://ciapi.cityindex.com/TradingAPI/useraccount/" )
        if acc_response.status_code == 200:
            accounts = acc_response.json().get("TradingAccounts", [])
            if accounts:
                account_id = accounts[0]["TradingAccountId"]
                print(f"📌 Using Account ID: {account_id}")
            else:
                print("❌ No trading accounts found.")
        else:
            print(f"❌ Failed to fetch accounts: {acc_response.text}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)

def place_order(order_type):
    global account_id
    if not account_id:
        print("❌ Cannot place order without a valid account ID")
        return

    url = "https://ciapi.cityindex.com/TradingAPI/order/newtradeorder"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "MarketId": 401484347,  # EUR/USD
        "Direction": "buy" if order_type == "BUY" else "sell",
        "Quantity": 1000,
        "TradingAccountId": account_id,
        "PositionMethodId": 1,
        "AuditId": "bot"
    }

    response = session.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"✅ {order_type} order placed successfully")
    else:
        print(f"❌ Failed to place {order_type} order: {response.status_code}")
        print(response.text)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"🚨 TradingView Alert Received: {data}")
    message = data.get("message")

    if "BUY" in message.upper():
        place_order("BUY")
    elif "SELL" in message.upper():
        place_order("SELL")
    else:
        print("⚠️ Unknown command in message")
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    login_to_forex()
    app.run(host="0.0.0.0", port=10000)
