# OANDA Forex Bot
# Risk: $200/trade, TP: 20 pips, SL: 10 pips, trailing SL +5 at +10
# Pairs: EUR/USD, GBP/USD, USD/JPY, USD/CHF
# Live on demo OANDA account

import requests
import time
import pandas as pd

# CONFIG
ACCOUNT_ID = "101-001-31681050-001"
API_KEY = "b02fade68c4d663a99df9ea55149581c-56d0c6dd9202d0d126d034f6d123adcb"
USE_PRACTICE = True
RISK_USD = 200
STOP_LOSS_PIPS = 10
TAKE_PROFIT_PIPS = 20
TRAIL_TRIGGER_PIPS = 10
TRAIL_SL_PIPS = 5
PAIRS = ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF"]
MAX_TRADES = 4

BASE_URL = "https://api-fxpractice.oanda.com" if USE_PRACTICE else "https://api-fxtrade.oanda.com"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Position sizing (based on pip value of ~$10 per lot)
def calculate_lot_size(risk_usd, stop_loss_pips):
    return round(risk_usd / (stop_loss_pips * 10), 2)

# Fetch candle data and compute EMA + VWAP
def get_indicators(pair, count=50):
    url = f"{BASE_URL}/v3/instruments/{pair}/candles?count={count}&granularity=M5&price=M"
    r = requests.get(url, headers=HEADERS)
    candles = r.json()['candles']
    closes = [float(c['mid']['c']) for c in candles if c['complete']]
    highs = [float(c['mid']['h']) for c in candles if c['complete']]
    lows = [float(c['mid']['l']) for c in candles if c['complete']]
    vols = [int(c['volume']) for c in candles if c['complete']]

    df = pd.DataFrame({
        'close': closes,
        'high': highs,
        'low': lows,
        'volume': vols
    })

    df['ema_9'] = df['close'].ewm(span=9).mean()
    df['ema_21'] = df['close'].ewm(span=21).mean()
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

# Determine entry signal

def check_entry_signal(df):
    if len(df) < 22:
        return False, None

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    # Buy if EMA9 crossed above EMA21 and price is above VWAP
    if previous['ema_9'] < previous['ema_21'] and latest['ema_9'] > latest['ema_21'] and latest['close'] > latest['vwap']:
        return True, "buy"

    # Sell if EMA9 crossed below EMA21 and price is below VWAP
    if previous['ema_9'] > previous['ema_21'] and latest['ema_9'] < latest['ema_21'] and latest['close'] < latest['vwap']:
        return True, "sell"

    return False, None

# Get mid price

def get_price(pair):
    url = f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}/pricing?instruments={pair}"
    r = requests.get(url, headers=HEADERS)
    prices = r.json()
    bids = float(prices['prices'][0]['bids'][0]['price'])
    asks = float(prices['prices'][0]['asks'][0]['price'])
    return (bids + asks) / 2

# Place a trade

def place_trade(pair, units, side, sl_pips, tp_pips):
    price = get_price(pair)
    sl = price - sl_pips * 0.0001 if side == "buy" else price + sl_pips * 0.0001
    tp = price + tp_pips * 0.0001 if side == "buy" else price - tp_pips * 0.0001

    data = {
        "order": {
            "instrument": pair,
            "units": str(units if side == "buy" else -units),
            "type": "MARKET",
            "positionFill": "DEFAULT",
            "takeProfitOnFill": {"price": f"{tp:.5f}"},
            "stopLossOnFill": {"price": f"{sl:.5f}"},
            "clientExtensions": {"tag": "#ProjectCIPHER-FX"}
        }
    }

    url = f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}/orders"
    r = requests.post(url, headers=HEADERS, json=data)
    return r.json()

# Main loop
while True:
    try:
        for pair in PAIRS:
            print(f"Checking {pair} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            df = get_indicators(pair)
            signal, side = check_entry_signal(df)

            if signal:
                lot_size = calculate_lot_size(RISK_USD, STOP_LOSS_PIPS)
                units = int(lot_size * 100000)
                print(f"Signal for {pair}: {side.upper()} — placing trade")
                result = place_trade(pair, units, side, STOP_LOSS_PIPS, TAKE_PROFIT_PIPS)
                print(result)
            else:
                print(f"No signal for {pair}")

            time.sleep(2)

        print("Cycle complete. Waiting 1 minute...")
        time.sleep(60)

    except Exception as e:
        print("Error:", e)
        time.sleep(60)
