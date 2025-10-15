from django.utils import timezone
from telebot import types, TeleBot
from bot.utils.constants import CHAT_ID_FOR_NOTIFIER
from subscriptions.models import Subscription
from subscriptions.utils import refresh_user_active_status
from users.models import User
import json

def check_expired_subscriptions(bot: TeleBot = None):
    now = timezone.now()
    subscriptions = Subscription.objects.filter(is_checked=False, expire_time__lt=now)

    for subscription in subscriptions:
        # Mark this subscription as processed
        subscription.is_checked = True
        subscription.save(update_fields=["is_checked"])

        # Refresh user's active status based on remaining subscriptions
        changed = refresh_user_active_status(subscription.user)

        # Notify only if user became inactive (no active subscriptions left)
        if bot and subscription.user.telegram_id and not subscription.user.is_active:
            try:
                bot.send_message(
                    subscription.user.telegram_id,
                    subscription.user.text.your_subscription_is_expired
                )
            except Exception as e:
                print(f"Xatolik: {e}")

    # Additionally handle admin manual activations stored in user.data
    admins = User.objects.filter(is_admin=True, is_active=True)
    for admin_user in admins:
        try:
            data = json.loads(admin_user.data) if admin_user.data else {}
        except Exception:
            data = {}
        admin_exp = data.get('admin_expires_at')
        if not admin_exp:
            continue
        if admin_exp == 'infinite':
            continue
        try:
            from django.utils import timezone as tz
            exp = tz.datetime.fromisoformat(admin_exp)
            if tz.is_naive(exp):
                exp = exp.replace(tzinfo=tz.utc)
        except Exception:
            continue
        if exp < now:
            # Deactivate admin whose manual activation expired
            admin_user.is_active = False
            admin_user.save(update_fields=["is_active"])
            # Optional: notify admin
            if bot and admin_user.telegram_id:
                try:
                    bot.send_message(
                        admin_user.telegram_id,
                        getattr(admin_user.text, 'your_subscription_is_expired', 'Obuna muddati tugadi.')
                    )
                except Exception as e:
                    print(f"Admin notify error: {e}")

def initializer_channel_post_handlers(bot: TeleBot):
    @bot.channel_post_handler(regexp="^#notify")
    def channel_post_handler(message: types.Message):
        if message.chat.id == CHAT_ID_FOR_NOTIFIER:
            bot.send_message(
                285710521,
                "Kanaldan xabar o'qildi va '#notify' topildi!"
            )
            check_expired_subscriptions(bot)
