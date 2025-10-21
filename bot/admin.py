from django.contrib import admin

from bot import models
from django.utils import timezone
from telebot import TeleBot
from telebot import types as ttypes
from bot.utils.constants import TOKEN
from users.models import User
from telebot.apihelper import ApiException


@admin.register(models.Constant)
class ConstantAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'key',
        'data',
        'added_time',
        'last_updated_time',
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]


@admin.register(models.Text)
class TextAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'language',
        'added_time',
        'last_updated_time',
    ]
    search_fields = [
        'id',
        'language',
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]


@admin.register(models.Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = ['id', 'title', 'is_sent', 'sent_at', 'added_time']
    search_fields = ['id', 'title', 'text']
    list_filter = ['is_sent']
    readonly_fields = ['is_sent', 'sent_at', 'added_time', 'last_updated_time']
    actions = ['send_now']

    def send_now(self, request, queryset):
        bot = TeleBot(TOKEN, parse_mode='html')

        def build_markup(obj: models.Announcement):
            if obj.button_text and obj.button_url:
                kb = ttypes.InlineKeyboardMarkup()
                kb.add(ttypes.InlineKeyboardButton(text=obj.button_text, url=obj.button_url))
                return kb
            return None

        total = 0
        users = list(User.objects.all())
        for obj in queryset:
            # Skip already sent announcements to avoid duplicates
            if obj.is_sent:
                continue
            markup = build_markup(obj)
            delivered = 0
            retry_users = []
            for user in users:
                try:
                    if obj.video:
                        with obj.video.open('rb') as f:
                            bot.send_video(user.telegram_id, f, caption=obj.text or None, reply_markup=markup)
                    elif obj.photo:
                        with obj.photo.open('rb') as f:
                            bot.send_photo(user.telegram_id, f, caption=obj.text or None, reply_markup=markup)
                    else:
                        bot.send_message(user.telegram_id, obj.text or obj.title, reply_markup=markup)
                    delivered += 1
                    # gentle pacing to avoid flood limits
                    import time; time.sleep(0.05)
                except ApiException as e:
                    err = str(e.args)
                    if "deactivated" in err or "blocked by the user" in err:
                        user.is_active = False
                        user.save(update_fields=["is_active"])
                    else:
                        retry_users.append(user)
            # Optional simple retry loop similar to sending_post
            for user in retry_users:
                try:
                    if obj.video:
                        with obj.video.open('rb') as f:
                            bot.send_video(user.telegram_id, f, caption=obj.text or None, reply_markup=markup)
                    elif obj.photo:
                        with obj.photo.open('rb') as f:
                            bot.send_photo(user.telegram_id, f, caption=obj.text or None, reply_markup=markup)
                    else:
                        bot.send_message(user.telegram_id, obj.text or obj.title, reply_markup=markup)
                    delivered += 1
                    import time; time.sleep(0.05)
                except Exception:
                    # Give up after one retry
                    pass
            obj.is_sent = True
            obj.sent_at = timezone.now()
            obj.save(update_fields=["is_sent", "sent_at"])
            total += delivered
        self.message_user(request, f"Yuborildi: {len(queryset)} ta e'lon, jami yetkazildi: {total} ta xabar.")
    send_now.short_description = "Tanlangan e'lon(lar)ni barcha foydalanuvchilarga yuborish"
