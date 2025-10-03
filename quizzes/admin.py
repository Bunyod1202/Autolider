from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin

from quizzes import models


class ThemeFilter(AutocompleteFilter):
    title = 'Theme'
    field_name = 'theme'


class OptionTabularInline(admin.TabularInline):
    model = models.Option
    extra = 0
    fields = [
        'text_uz',
        'text_ru',
        'is_correct',
        'added_time',
        'last_updated_time',
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]


@admin.register(models.Theme)
class ThemeAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'name_uz',
        'name_ru',
        'order',
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


@admin.register(models.Quiz)
class QuizAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id',
        'theme',
        'question_uz',
        'question_ru',
        'image_url',
        'is_active',
        'added_time',
        'last_updated_time',
    ]
    list_filter = [
        ThemeFilter,
        'is_active',
    ]
    search_fields = [
        'question_uz',
        'question_ru',
    ]
    autocomplete_fields = [
        'theme',
    ]
    inlines = [
        OptionTabularInline,
    ]
    readonly_fields = [
        'added_time',
        'last_updated_time',
    ]
