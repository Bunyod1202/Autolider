from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin

from payments import models


class UserFilter(AutocompleteFilter):
    title = 'User'
    field_name = 'user'


@admin.register(models.Provider)
class ProviderAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'name_uz',
        'name_ru',
        'data',
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
        'data',
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'user',
        'provider',
        'subscription',
        'provider_transaction_id',
        'amount',
        'added_time',
        'last_updated_time',
    ]
    list_filter = [
        UserFilter,
        'provider',
    ]
    search_fields = [
        'id',
        'provider_transaction_id',
        'amount',
    ]
    autocomplete_fields = [
        'user',
        'provider',
        'subscription',
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]
