import requests
import time
from bot.factory import bot_initializer
from bot.utils.constants import TOKEN

# Webhook ni o'chirish
print("Webhook o'chirilmoqda...")
response = requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
print("Natija:", response.json())
time.sleep(3)

# Botni ishga tushirish
print("Bot ishga tushirilmoqda...")
bot = bot_initializer(TOKEN)
print("✅ Bot ishlayapti!")
print("📱 Telegram: @avtolider_test_bot ga /start yuboring")
bot.infinity_polling()
