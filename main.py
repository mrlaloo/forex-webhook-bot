import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load OANDA credentials
OANDA_API_KEY = os.getenv('OANDA_API_KEY')
OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')

# API endpoints
OANDA_ORDER_URL = f"https://api-fxpractice.oanda.com/v3/accounts/{OANDA_ACCOUNT_ID}/orders"
OANDA_TRADE_URL = f"https://api-fxpractice.oanda.com/v3/accounts/{OANDA_ACCOUNT_ID}/openTrades"
OANDA_CLOSE_TRADE_URL = f"https://api-fxpractice.oanda.com/v3/accounts/{OANDA_ACCOUNT_ID}/trades"

# Headers
HEADERS = {
    "Authorization": f"Bearer {OANDA_API_KEY}",
    "Content-Type": "application/json"
}

# Parameters
TRAIL_PIPS = 10  # pip distance to trail profit

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

    order_data = {
        "order": {
            "instrument": "EUR_USD",
            "units": units,
            "type": "MARKET",
            "timeInForce": "FOK",
            "positionFill": "DEFAULT"
        }
    }

    response = requests.post(OANDA_ORDER_URL, headers=HEADERS, json=order_data)
    print("Order Response:", response.json())
    return jsonify(response.json())

@app.route("/watchdog", methods=["GET"])
def watchdog():
    price_url = f"https://api-fxpractice.oanda.com/v3/accounts/{OANDA_ACCOUNT_ID}/pricing?instruments=EUR_USD"
    r = requests.get(price_url, headers=HEADERS)
    try:
        prices = r.json()["prices"]
        print("Watchdog price check:", prices)
        return jsonify({"status": "ok", "prices": prices})
    except KeyError:
        print("Watchdog error: 'prices' field missing")
        print("Full response:", r.json())
        return jsonify({"status": "error", "detail": "'prices' field missing"}), 500

@app.route("/trail", methods=["GET"])
def trail():
    trades = requests.get(OANDA_TRADE_URL, headers=HEADERS).json()
    if "trades" not in trades:
        return jsonify({"error": "No open trades found"}), 404

    for trade in trades["trades"]:
        trade_id = trade["id"]
        current_price = float(trade["price"])
        unrealized_pl = float(trade["unrealizedPL"])

        # OANDA reports in account currency, pip approximation is 0.0001 for EURUSD
        profit_pips = unrealized_pl / 0.1

        print(f"Checking trade {trade_id} @ {current_price} | PL: {unrealized_pl} ({profit_pips:.1f} pips)")

        if profit_pips >= TRAIL_PIPS:
            close_url = f"{OANDA_CLOSE_TRADE_URL}/{trade_id}/close"
            close_response = requests.put(close_url, headers=HEADERS)
            print(f"Trade {trade_id} closed: {close_response.json()}")

    return jsonify({"status": "trailing logic executed"})

if __name__ == "__main__":
    app.run(debug=True)
