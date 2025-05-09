# === Flask Bot with TP & SL for OANDA ===
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

# === Configurable TP/SL ===
TAKE_PROFIT_PIPS = 40
STOP_LOSS_PIPS = 20

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
    units = "1000" if side == "buy" else "-1000"

    # Simulate price (can be real-time fetched for precision)
    price = 1.1250
    pip = 0.0001
    tp_price = price + TAKE_PROFIT_PIPS * pip if side == "buy" else price - TAKE_PROFIT_PIPS * pip
    sl_price = price - STOP_LOSS_PIPS * pip if side == "buy" else price + STOP_LOSS_PIPS * pip

    order = {
        "order": {
            "units": units,
            "instrument": "EUR_USD",
            "timeInForce": "FOK",
            "type": "MARKET",
            "positionFill": "DEFAULT",
            "takeProfitOnFill": {"price": f"{tp_price:.5f}"},
            "stopLossOnFill": {"price": f"{sl_price:.5f}"}
        }
    }

    response = requests.post(OANDA_URL, headers=HEADERS, json=order)
    print("Order Response:", response.text)
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(debug=True)
