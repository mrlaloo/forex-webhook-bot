import os
import json
import requests
import threading
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

OANDA_API_KEY = os.getenv('OANDA_API_KEY')
OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')
OANDA_URL = f"https://api-fxpractice.oanda.com/v3/accounts/{OANDA_ACCOUNT_ID}/"
HEADERS = {
    "Authorization": f"Bearer {OANDA_API_KEY}",
    "Content-Type": "application/json"
}

# Store trades and their max profit prices
open_trades = {}  # trade_id: {"entry": float, "max_price": float}
TRAILING_STOP_PIPS = 10  # Set trailing stop in pips
PIP_VALUE = 0.0001  # For EUR/USD

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

    order = {
        "order": {
            "instrument": "EUR_USD",
            "units": units,
            "type": "MARKET",
            "timeInForce": "FOK",
            "positionFill": "DEFAULT"
        }
    }

    response = requests.post(OANDA_URL + "orders", headers=HEADERS, json=order)
    if response.status_code == 201:
        order_data = response.json()
        trade_id = order_data["orderCreateTransaction"]["id"]
        price = float(order_data["orderCreateTransaction"]["price"])
        open_trades[trade_id] = {"entry": price, "max_price": price, "side": side}
        print(f"Trade opened: {trade_id}, entry: {price}")
    else:
        print("Order failed:", response.text)

    return jsonify({"status": "executed"}), 200

def trailing_watchdog():
    while True:
        time.sleep(30)  # Check every 30s
        try:
            r = requests.get(OANDA_URL + "openPositions", headers=HEADERS)
            positions = r.json().get("positions", [])

            for pos in positions:
                if pos["instrument"] != "EUR_USD":
                    continue

                side = "buy" if float(pos["long"]["units"]) != 0 else "sell"
                unrealized_pl = float(pos["unrealizedPL"])
                price = float(pos["long"]["averagePrice"] if side == "buy" else pos["short"]["averagePrice"])
                market_price = get_current_price()

                trailing_stop = TRAILING_STOP_PIPS * PIP_VALUE
                if side == "buy":
                    max_price = max(open_trades.get(pos["pl"]["tradeID"], {}).get("max_price", price), market_price)
                    open_trades[pos["pl"]["tradeID"]]["max_price"] = max_price
                    if market_price < (max_price - trailing_stop):
                        close_trade(pos["pl"]["tradeID"], side)
                else:
                    min_price = min(open_trades.get(pos["pl"]["tradeID"], {}).get("max_price", price), market_price)
                    open_trades[pos["pl"]["tradeID"]]["max_price"] = min_price
                    if market_price > (min_price + trailing_stop):
                        close_trade(pos["pl"]["tradeID"], side)

        except Exception as e:
            print("Watchdog error:", e)

def get_current_price():
    r = requests.get("https://api-fxpractice.oanda.com/v3/instruments/EUR_USD/price", headers=HEADERS)
    price_data = r.json()["prices"][0]
    return float(price_data["asks"][0]["price"])

def close_trade(trade_id, side):
    data = {"units": "1000" if side == "buy" else "-1000"}
    r = requests.put(OANDA_URL + f"positions/EUR_USD/close", headers=HEADERS, json=data)
    print(f"Closed trade {trade_id}: {r.status_code}, {r.text}")

# Start trailing stop watcher in background
threading.Thread(target=trailing_watchdog, daemon=True).start()

if __name__ == "__main__":
    app.run(port=5000)
