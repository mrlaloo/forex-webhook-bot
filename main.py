import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# Environment variables
OANDA_API_KEY = os.getenv("OANDA_API_KEY")
OANDA_ACCOUNT_ID = os.getenv("FOREX_ACCOUNT_ID")

# OANDA API endpoint
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
        return {"error": "No message field found"}, 400

    message = data["message"].strip().upper()

    if message == "BUY EURUSD":
        return place_order("EUR_USD", "buy")
    elif message == "SELL EURUSD":
        return place_order("EUR_USD", "sell")
    else:
        return {"error": "Unknown message"}, 400

def place_order(instrument, side):
    order_data = {
        "order": {
            "units": "100" if side == "buy" else "-100",
            "instrument": instrument,
            "timeInForce": "FOK",
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }
    }

    response = requests.post(OANDA_URL, headers=HEADERS, data=json.dumps(order_data))
    print("Order Response:", response.text)

    if response.status_code == 201:
        return {"status": "Order placed successfully"}, 201
    else:
        return {"error": response.text}, response.status_code

if __name__ == "__main__":
    app.run(debug=True)
