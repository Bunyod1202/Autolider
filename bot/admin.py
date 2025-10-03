from django.contrib import admin

from bot import models


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
