from django.utils import timezone
from telebot import types, TeleBot
from bot.utils.constants import CHAT_ID_FOR_NOTIFIER
from subscriptions.models import Subscription

def check_expired_subscriptions(bot: TeleBot = None):
    now = timezone.now()
    subscriptions = Subscription.objects.filter(is_checked=False, expire_time__lt=now)

    for subscription in subscriptions:
        subscription.user.is_active = False
        subscription.user.save()
        subscription.is_checked = True
        subscription.save()

        if bot and subscription.user.telegram_id:
            try:
                bot.send_message(
                    subscription.user.telegram_id,
                    subscription.user.text.your_subscription_is_expired
                )
            except Exception as e:
                print(f"Xatolik: {e}")

def initializer_channel_post_handlers(bot: TeleBot):
    @bot.channel_post_handler(regexp="^#notify")
    def channel_post_handler(message: types.Message):
        if message.chat.id == CHAT_ID_FOR_NOTIFIER:
            bot.send_message(
                285710521,
                "Kanaldan xabar o'qildi va '#notify' topildi!"
            )
            check_expired_subscriptions(bot)
