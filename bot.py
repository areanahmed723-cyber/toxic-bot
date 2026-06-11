import asyncio
import logging
import random
from datetime import datetime

from telegram import Bot
from telegram.constants import ParseMode

# ========== কনফিগারেশন ==========
BOT_TOKEN = "8931648464:AAFJsROE9zpYcdXsuXhWn-PY5ld6rg_gtGg"
CHANNEL_ID = "-1003959054969"
ASSET = "USDARS-OTCq"
TIMEFRAME = "M1"

price = 1480.75

def update_price():
    global price
    change = (random.random() - 0.5) * 0.002
    price *= (1 + change)
    return round(price, 2)

def generate_signal():
    return random.choice(["CALL", "PUT"])

def get_trade_result():
    return "WIN" if random.random() < 0.7 else "LOSS"

def format_signal_message(direction, current_price, timestamp):
    arrow = "🟢" if direction == "CALL" else "🔴"
    return f"📊 {ASSET}\n🕓 {timestamp}\n⏳ {TIMEFRAME}\n{arrow} {direction}\n🎯 {current_price}"

def format_result_message(result, timestamp):
    status = "✔️✔️✔️ WIN" if result == "WIN" else "❌❌❌ LOSS"
    msg = f"Toxic Pro\n"
    msg += f"**!! Toxic Pro Signal !!**\n\n"
    msg += f"{ASSET}\n"
    msg += f"{timestamp}\n\n"
    msg += f"{status}"
    return msg

async def send_signal_and_result():
    bot = Bot(token=BOT_TOKEN)
    current_price = update_price()
    direction = generate_signal()
    signal_time = datetime.now().strftime("%H:%M")
    await bot.send_message(chat_id=CHANNEL_ID, text=format_signal_message(direction, current_price, signal_time), parse_mode=ParseMode.MARKDOWN)
    logging.info(f"Signal sent: {direction}")
    await asyncio.sleep(60)
    result = get_trade_result()
    result_time = datetime.now().strftime("%H:%M")
    await bot.send_message(chat_id=CHANNEL_ID, text=format_result_message(result, result_time), parse_mode=ParseMode.MARKDOWN)
    logging.info(f"Result sent: {result}")

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Bot started")
    while True:
        await send_signal_and_result()
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
