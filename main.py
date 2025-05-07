from flask import Flask, request
import datetime

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    message = data.get('message', '')

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] 🔔 TradingView Alert Received: {message}")

    if "BUY EURUSD" in message.upper():
        print("🚀 Simulated Trade: BUY EURUSD")
    elif "SELL EURUSD" in message.upper():
        print("🔻 Simulated Trade: SELL EURUSD")
    else:
        print("⚠️ Unrecognized message format")

    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
