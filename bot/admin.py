from django.contrib import admin

from bot import models
from django.utils import timezone
from bot.utils.helpers import kick_off_announcement_send


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
        started = 0
        for obj in queryset:
            if obj.is_sent:
                continue
            kick_off_announcement_send(obj.id)
            started += 1
        if started:
            self.message_user(request, f"{started} ta e'lon yuborish jarayoni boshlandi. Natija yakunlangach 'is_sent' yangilanadi.")
        else:
            self.message_user(request, "Yangi yuborish boshlanmadi (hammasi yuborilgan yoki tanlanmadi).")
    send_now.short_description = "Tanlangan e'lon(lar)ni barcha foydalanuvchilarga yuborish"
