import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# Load credentials from environment
FOREX_EMAIL = os.environ.get("FOREX_EMAIL")
FOREX_PASSWORD = os.environ.get("FOREX_PASSWORD")
FOREX_ACCOUNT_ID = os.environ.get("FOREX_ACCOUNT_ID")

# Constants
LOGIN_URL = "https://api-demo.forex.com/auth/token"
ORDER_URL = f"https://api-demo.forex.com/accounts/{FOREX_ACCOUNT_ID}/orders"
TOKEN = None

def login():
    global TOKEN
    payload = {
        "identifier": FOREX_EMAIL,
        "password": FOREX_PASSWORD
    }
    response = requests.post(LOGIN_URL, json=payload)
    if response.status_code == 200:
        TOKEN = response.json().get("access_token")
        print("✅ Logged in to FOREX.com API")
    else:
        print("❌ Login failed", response.text)


def place_order(order_type):
    if not TOKEN:
        login()
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    order_data = {
        "market": "EUR/USD",
        "quantity": 1000,
        "action": "BUY" if order_type == "BUY" else "SELL",
        "orderType": "Market"
    }

    response = requests.post(ORDER_URL, headers=headers, json=order_data)
    if response.status_code == 201:
        print(f"✅ {order_type} order placed successfully")
    else:
        print(f"❌ Failed to place {order_type} order", response.text)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("🚨 TradingView Alert Received:", data)

    if not data or "message" not in data:
        return {"status": "ignored", "reason": "no valid message"}, 400

    message = data["message"].strip().upper()
    if message == "BUY EURUSD":
        place_order("BUY")
    elif message == "SELL EURUSD":
        place_order("SELL")
    else:
        return {"status": "ignored", "reason": "unknown command"}, 400

    return {"status": "success"}, 200


if __name__ == "__main__":
    login()
    app.run(debug=True, port=5000)
