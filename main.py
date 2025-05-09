import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

OANDA_API_KEY = os.getenv('OANDA_API_KEY')
OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')

OANDA_URL = f"https://api-fxpractice.oanda.com/v3/accounts/{OANDA_ACCOUNT_ID}/orders"
HEADERS = {
    "Authorization": f"Bearer {OANDA_API_KEY}",
    "Content-Type": "application/json"
}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Alert Received:", data)

    if "message" not in data:
        return jsonify({"error": "Missing message field"}), 400

    signal = data["message"].strip().upper()
    if signal not in ["BUY EURUSD", "SELL EURUSD"]:
        return jsonify({"error": "Invalid signal format"}), 400

    side = "buy" if "BUY" in signal else "sell"

    order_data = {
        "order": {
            "instrument": "EUR_USD",
            "units": "1000" if side == "buy" else "-1000",
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }
    }

    response = requests.post(OANDA_URL, headers=HEADERS, json=order_data)
    print("Order Response:", response.text)

    if response.status_code != 201:
        return jsonify({"error": "Order placement failed", "details": response.text}), 500

    return jsonify({"message": "Order placed successfully"})
