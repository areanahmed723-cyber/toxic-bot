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

# সিমুলেটেড মার্কেট
def update_price():
    global price
    change = (random.random() - 0.5) * 0.002
    price *= (1 + change)
    return round(price, 2)

# সিগন্যাল জেনারেশন (CALL/PUT)
def generate_signal():
    # র্যান্ডম – আপনি পরে RSI/MACD লজিক বসাতে পারেন
    return random.choice(["CALL", "PUT"])

# WIN/LOSS নির্ধারণ (প্রথমে না জানিয়ে পরে পাঠাবে)
# এখানে সিমুলেটেড – আপনি বাস্তব ডাটা বসাতে পারেন
def get_trade_result():
    # 70% WIN, 30% LOSS (উদাহরণ)
    return "WIN" if random.random() < 0.7 else "LOSS"

# ইমোজি সহ সিগন্যাল মেসেজ
def format_signal_message(direction, current_price, timestamp):
    if direction == "CALL":
        arrow_emoji = "🟢"
    else:
        arrow_emoji = "🔴"
    
    msg = f"📊 {ASSET}\n"
    msg += f"🕓 {timestamp}\n"
    msg += f"⏳ {TIMEFRAME}\n"
    msg += f"{arrow_emoji} {direction}\n"
    msg += f"🎯 {current_price}"
    return msg

# রেজাল্ট মেসেজ (WIN/LOSS)
def format_result_message(result, timestamp):
    if result == "WIN":
        status = "✔️✔️✔️ WIN"
    else:
        status = "❌❌❌ LOSS"
    
    msg = f"Secret Trading Bot FREE (Xadikul)\n"
    msg += f"** [!!] Quotex Otc Bot [!!] **\n\n"
    msg += f"{ASSET}\n"
    msg += f"{timestamp}\n\n"
    msg += f"{status}"
    return msg

# সিগন্যাল ও পরে রেজাল্ট পাঠানোর ফাংশন
async def send_signal_and_result():
    bot = Bot(token=BOT_TOKEN)
    
    # ১. সিগন্যাল জেনারেট
    current_price = update_price()
    direction = generate_signal()
    signal_time = datetime.now().strftime("%H:%M")
    signal_msg = format_signal_message(direction, current_price, signal_time)
    
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=signal_msg,
        parse_mode=ParseMode.MARKDOWN
    )
    logging.info(f"Signal sent: {direction} at {current_price}")
    
    # ২. এক্সপাইরি সময় (M1 = 1 মিনিট) অপেক্ষা
    await asyncio.sleep(60)
    
    # ৩. রেজাল্ট জেনারেট ও পাঠানো
    result = get_trade_result()
    result_time = datetime.now().strftime("%H:%M")
    result_msg = format_result_message(result, result_time)
    
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=result_msg,
        parse_mode=ParseMode.MARKDOWN
    )
    logging.info(f"Result sent: {result} for {direction}")

# মেইন লুপ (প্রতি ২ মিনিটে একটি সিগন্যাল+রেজাল্ট চক্র)
async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Bot started with emoji + WIN/LOSS result")
    while True:
        await send_signal_and_result()
        # পরবর্তী সিগন্যালের আগে কিছু গ্যাপ (যাতে ওভারল্যাপ না হয়)
        await asyncio.sleep(10)   # ১০ সেকেন্ড গ্যাপ, আপনি বাড়াতে পারেন

if __name__ == "__main__":
    asyncio.run(main())