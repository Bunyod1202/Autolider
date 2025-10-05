from django.core.management.base import BaseCommand
from django.utils import timezone
from telebot import TeleBot
from bot.utils.constants import TOKEN
from subscriptions.models import Subscription

class Command(BaseCommand):
    help = "Check expired subscriptions and deactivate users"

    def handle(self, *args, **options):
        bot = TeleBot(TOKEN)
        now = timezone.now()
        subscriptions = Subscription.objects.filter(is_checked=False, expire_time__lt=now)

        count = 0
        for subscription in subscriptions:
            subscription.user.is_active = False
            subscription.user.save()
            subscription.is_checked = True
            subscription.save()
            count += 1

            if subscription.user.telegram_id:
                try:
                    bot.send_message(
                        subscription.user.telegram_id,
                        "⏰ Sizning obunangiz muddati tugadi. Iltimos, qayta to‘lovni amalga oshiring."
                    )
                except Exception as e:
                    print(f"Xatolik: {e}")

        self.stdout.write(self.style.SUCCESS(f"✅ {count} ta obuna tekshirildi va tugaganlari o‘chirildi."))
