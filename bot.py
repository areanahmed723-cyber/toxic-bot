import asyncio
import logging
import random
from datetime import datetime
from threading import Thread

from flask import Flask, Response
from telegram import Bot
from telegram.constants import ParseMode

# ========== কনফিগারেশন ==========
BOT_TOKEN = "8931648464:AAFJsROE9zpYcdXsuXhWn-PY5ld6rg_gtGg"
CHANNEL_ID = "-1003959054969"

# ========== সব অ্যাসেটের তালিকা (Quotex-এর সব) ==========
ASSETS = {
    # Forex
    "EUR/USD": {"volatility": 0.0015, "base_price": 1.0850, "type": "Forex"},
    "GBP/USD": {"volatility": 0.0015, "base_price": 1.2680, "type": "Forex"},
    "USD/JPY": {"volatility": 0.0015, "base_price": 148.20, "type": "Forex"},
    "AUD/USD": {"volatility": 0.0015, "base_price": 0.6640, "type": "Forex"},
    "USD/CAD": {"volatility": 0.0015, "base_price": 1.3580, "type": "Forex"},
    "EUR/GBP": {"volatility": 0.0015, "base_price": 0.8550, "type": "Forex"},
    # Crypto
    "BTC/USD": {"volatility": 0.025, "base_price": 62500, "type": "Crypto"},
    "ETH/USD": {"volatility": 0.018, "base_price": 3120, "type": "Crypto"},
    "LTC/USD": {"volatility": 0.015, "base_price": 82.5, "type": "Crypto"},
    # OTC
    "EUR/USD OTC": {"volatility": 0.0012, "base_price": 1.0852, "type": "OTC"},
    "GBP/USD OTC": {"volatility": 0.0012, "base_price": 1.2678, "type": "OTC"},
    "USD/JPY OTC": {"volatility": 0.0012, "base_price": 148.25, "type": "OTC"},
    # Commodity
    "GOLD": {"volatility": 0.004, "base_price": 2350, "type": "Commodity"},
    "SILVER": {"volatility": 0.003, "base_price": 28.4, "type": "Commodity"},
    "OIL": {"volatility": 0.012, "base_price": 82.3, "type": "Commodity"},
}

# প্রতিটি অ্যাসেটের জন্য আলাদা প্রাইস হিস্টোরি
price_history = {asset: [data["base_price"]] * 30 for asset, data in ASSETS.items()}
current_prices = {asset: data["base_price"] for asset, data in ASSETS.items()}

# টাইমফ্রেম (সেকেন্ডে)
TIMEFRAMES = {
    "1M": 60,
    "2M": 120,
    "5M": 300,
    "10M": 600
}

# ========== ফ্লাস্ক হেলথ চেক ==========
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return Response("OK", status=200)

def run_http_server():
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ========== মার্কেট সিমুলেশন ==========
def update_price(asset):
    """অ্যাসেটের বর্তমান মূল্য আপডেট করে"""
    vol = ASSETS[asset]["volatility"]
    curr = current_prices[asset]
    change = (random.random() - 0.5) * vol
    new_price = curr + change
    # বাউন্ড চেক
    if asset in ["BTC/USD"] and new_price < 30000:
        new_price = 30000
    elif asset in ["GOLD"] and new_price < 2000:
        new_price = 2000
    elif "USD" in asset and new_price < 0.5:
        new_price = 0.5
    current_prices[asset] = new_price
    # হিস্টোরি আপডেট
    price_history[asset].append(new_price)
    if len(price_history[asset]) > 30:
        price_history[asset].pop(0)
    return new_price

def calculate_rsi(asset, period=14):
    hist = price_history[asset]
    if len(hist) < period + 1:
        return 50.0
    gains, losses = 0.0, 0.0
    for i in range(-period, 0):
        diff = hist[i] - hist[i-1]
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)

def get_macd_signal(asset):
    rsi = calculate_rsi(asset, 14)
    price = current_prices[asset]
    prev = price_history[asset][-2] if len(price_history[asset]) >= 2 else price
    mom = price - prev
    if rsi > 70 and mom > 0:
        return "BEAR"
    elif rsi < 30 and mom < 0:
        return "BULL"
    elif rsi > 70:
        return "BEAR"
    elif rsi < 30:
        return "BULL"
    elif mom > 0.0005:
        return "BULL"
    elif mom < -0.0005:
        return "BEAR"
    return "NEUTRAL"

def get_bollinger_signal(asset):
    rsi = calculate_rsi(asset, 20)
    if rsi > 75:
        return "UPPER"
    elif rsi < 25:
        return "LOWER"
    return "MID"

def get_stochastic_signal(asset):
    rsi = calculate_rsi(asset, 14)
    stoch = min(100, max(0, (rsi - 20) * 1.25))
    if stoch < 30:
        return "BULL"
    elif stoch > 70:
        return "BEAR"
    return "NEUTRAL"

def generate_signal(asset, timeframe_sec):
    """একটি অ্যাসেট ও টাইমফ্রেমের জন্য সিগন্যাল জেনারেট করে (CALL/PUT)"""
    rsi = calculate_rsi(asset)
    macd = get_macd_signal(asset)
    bb = get_bollinger_signal(asset)
    stoch = get_stochastic_signal(asset)
    
    bull_points, bear_points = 0, 0
    
    # RSI
    if rsi < 35: bull_points += 35
    elif rsi > 65: bear_points += 35
    elif rsi < 45: bull_points += 15
    elif rsi > 55: bear_points += 15
    
    # MACD
    if macd == "BULL": bull_points += 30
    elif macd == "BEAR": bear_points += 30
    
    # Bollinger
    if bb == "LOWER": bull_points += 25
    elif bb == "UPPER": bear_points += 25
    
    # Stochastic
    if stoch == "BULL": bull_points += 20
    elif stoch == "BEAR": bear_points += 20
    
    # Momentum (সরল)
    hist = price_history[asset]
    if len(hist) >= 2:
        mom = hist[-1] - hist[-2]
        if mom > 0: bull_points += 15
        elif mom < 0: bear_points += 15
    
    # র‍্যান্ডম নয়েজ
    bull_points += random.uniform(-5, 5)
    bear_points += random.uniform(-5, 5)
    
    total = bull_points + bear_points
    if total == 0:
        return "WAIT"
    
    bull_ratio = bull_points / total
    if bull_ratio >= 0.65:
        return "CALL"
    elif bull_ratio <= 0.35:
        return "PUT"
    else:
        return "WAIT"

def format_signal_message(asset, direction, current_price, timeframe_label):
    arrow = "🟢" if direction == "CALL" else "🔴"
    timestamp = datetime.now().strftime("%H:%M")
    msg = f"📊 {asset}\n🕓 {timestamp}\n⏳ {timeframe_label}\n{arrow} {direction}\n🎯 {round(current_price, 2)}"
    return msg

# ========== রোটেশন সিস্টেম ==========
asset_list = list(ASSETS.keys())
asset_index = 0

async def send_signals_for_asset():
    global asset_index
    asset = asset_list[asset_index]
    current_price = update_price(asset)
    
    # প্রতিটি টাইমফ্রেমের জন্য আলাদা সিগন্যাল জেনারেট ও পাঠান
    for tf_label, tf_sec in TIMEFRAMES.items():
        direction = generate_signal(asset, tf_sec)
        if direction != "WAIT":  # WAIT সিগন্যাল বাদ দিন
            msg = format_signal_message(asset, direction, current_price, tf_label)
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
            logging.info(f"Sent {direction} for {asset} ({tf_label}) at {current_price}")
        else:
            logging.info(f"WAIT for {asset} ({tf_label}) – nothing sent")
    
    # পরবর্তী অ্যাসেটে যান
    asset_index = (asset_index + 1) % len(asset_list)

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Toxic Pro Bot started – rotating all assets and timeframes")
    while True:
        await send_signals_for_asset()
        # প্রতিটি অ্যাসেটের জন্য ২ মিনিট (120 সেকেন্ড) অপেক্ষা করবে
        # এক চক্রে ১৫ অ্যাসেট × ৪ টাইমফ্রেম = ৬০ সিগন্যাল (WAIT বাদে)
        await asyncio.sleep(120)

if __name__ == "__main__":
    # HTTP সার্ভার চালু করুন (Render health check এর জন্য)
    server_thread = Thread(target=run_http_server, daemon=True)
    server_thread.start()
    asyncio.run(main())
