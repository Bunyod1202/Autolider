import os
import django

# Django muhitini sozlash
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avtolider_bot.settings")
django.setup()

from bot.handlers.channel_post import check_expired_subscriptions
check_expired_subscriptions()
