from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin

from subscriptions import models


class UserFilter(AutocompleteFilter):
    title = 'User'
    field_name = 'user'


@admin.register(models.Tariff)
class TariffAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'name_uz',
        'name_ru',
        'days',
        'price',
        'is_active',
        'added_time',
        'last_updated_time',
    ]
    list_filter = [
        'is_active',
    ]
    search_fields = [
        'id',
        'name_uz',
        'name_ru',
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]


@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'user',
        'tariff',
        'expire_time',
        'is_checked',
        'added_time',
        'last_updated_time',
    ]
    list_filter = [
        UserFilter,
        'tariff',
        'is_checked',
    ]
    search_fields = [
        'id',
    ]
    autocomplete_fields = [
        'user',
        'tariff',
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]
