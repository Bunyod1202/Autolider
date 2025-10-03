from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin

from users import models


class TextFilter(AutocompleteFilter):
    title = 'Text'
    field_name = 'text'


class UserFilter(AutocompleteFilter):
    title = 'User'
    field_name = 'user'


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'telegram_id',
        'full_name',
        'phone_number',
        'username',
        'text',
        'is_active',
        'is_admin',
        'step',
        'data',
        'added_time',
        'last_updated_time',
    ]
    list_filter = [
        TextFilter,
        'is_active',
        'is_admin',
        'step',
    ]
    search_fields = [
        'id',
        'telegram_id',
        'full_name',
        'phone_number',
        'username',
    ]
    autocomplete_fields = [
        'text'
    ]
    readonly_fields = [
        'step',
        'data',
        'added_time',
        'last_updated_time',
    ]


@admin.register(models.Log)
class LogAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'user',
        'reason',
        'text',
        'added_time',
    ]
    list_filter = [
        UserFilter,
        'reason',
    ]
    readonly_fields = [
        'added_time',
    ]
