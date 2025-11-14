from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin, messages
from django.http import JsonResponse, HttpRequest
from django.urls import path
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from uuid import uuid4
import os
from requests import post

from quizzes import models
from .forms import QuizAdminForm


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
    form = QuizAdminForm
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

    fields = [
        'theme',
        'question_uz',
        'question_ru',
        'image_upload',  # drag&drop file input (optional)
        'image_url',     # or paste a URL
        'is_active',
        'added_time',
        'last_updated_time',
    ]

    def save_model(self, request, obj, form, change):
        uploaded = form.cleaned_data.get('image_upload')
        if uploaded:
            try:
                file_bytes = uploaded.read()
                content_type = getattr(uploaded, 'content_type', 'image/jpeg') or 'image/jpeg'
                resp = post(
                    'https://telegra.ph/upload',
                    files={'file': ('file', file_bytes, content_type)},
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list) and data and 'src' in data[0]:
                    obj.image_url = f"https://telegra.ph{data[0]['src']}"
                    messages.success(request, 'Rasm Telegra.ph ga yuklandi va URL saqlandi.')
                else:
                    messages.error(request, 'Rasmni yuklashda kutilmagan javob qaytdi.')
            except Exception as e:
                messages.error(request, f"Rasmni yuklab bo'lmadi: {e}")
        super().save_model(request, obj, form, change)

    # Admin-only AJAX upload endpoint (stores file on server and returns absolute URL)
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('upload-image/', self.admin_site.admin_view(self.upload_image_view), name='quizzes_quiz_upload_image'),
        ]
        return custom + urls

    def upload_image_view(self, request: HttpRequest):
        if request.method != 'POST':
            return JsonResponse({'ok': False, 'error': 'Only POST allowed.'}, status=405)

        f = request.FILES.get('file')
        if not f:
            return JsonResponse({'ok': False, 'error': 'No file provided.'}, status=400)

        # Determine extension from name or content_type
        _, ext = os.path.splitext(f.name or '')
        if not ext:
            # crude fallback
            ext = '.jpg'

        filename = f"quizzes/{uuid4().hex}{ext}"
        try:
            saved_path = default_storage.save(filename, ContentFile(f.read()))
            # Build absolute URL for the saved media
            from django.conf import settings
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            # In admin, request has full host -> build absolute URL
            absolute_url = request.build_absolute_uri(f"{media_url}{saved_path}")
            return JsonResponse({'ok': True, 'url': absolute_url, 'path': saved_path})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)
