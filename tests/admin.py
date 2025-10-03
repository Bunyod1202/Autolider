from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin

from tests import models


class UserFilter(AutocompleteFilter):
    title = 'User'
    field_name = 'user'


class ThemeFilter(AutocompleteFilter):
    title = 'Theme'
    field_name = 'theme'


@admin.register(models.Test)
class TestAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'user',
        'theme',
        'quizzes_count',
        'correct_answers_count',
        'spent_seconds',
        'added_time',
        'last_updated_time',
    ]
    list_filter = [
        UserFilter,
        ThemeFilter,
    ]
    search_fields = [
        'id',
        'user__telegram_id',
        'user__full_name',
    ]
    filter_horizontal = [
        'selected_options',
    ]
    autocomplete_fields = [
        'user',
        'theme',
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]
