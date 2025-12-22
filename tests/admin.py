from django.contrib import admin
from django.contrib.admin.exceptions import AlreadyRegistered
from . import models


@admin.register(models.Test)
class TestAdmin(admin.ModelAdmin):
    date_hierarchy = 'added_time'
    list_display = [
        'id', 'user', 'theme', 'quizzes_count', 'correct_answers_count',
        'spent_seconds', 'added_time', 'last_updated_time',
    ]
    list_filter = ['user', 'theme']
    search_fields = ['id', 'user__telegram_id', 'user__full_name']
    filter_horizontal = ['selected_options']
    autocomplete_fields = ['user', 'theme']
    readonly_fields = ['added_time', 'last_updated_time']


class ExamAccessInline(admin.TabularInline):
    model = models.ExamAccess
    extra = 0
    autocomplete_fields = ['user']


class AttemptQuestionInline(admin.TabularInline):
    model = models.AttemptQuestion
    extra = 0
    fields = ['order', 'question', 'user_answer', 'is_correct']
    autocomplete_fields = ['question', 'user_answer']


class ExamAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ['id', 'title', 'type', 'date', 'question_count', 'is_active', 'added_time', 'last_updated_time']
    list_filter = ['type', 'is_active']
    filter_horizontal = ['topics']
    search_fields = ['title']
    readonly_fields = ['added_time', 'last_updated_time']
    fieldsets = (
        (None, {'fields': ('title', 'type', 'date', 'question_count', 'is_active')}),
        ('Mavzular (faqat MID uchun)', {'fields': ('topics',)}),
    )
    inlines = [ExamAccessInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # MID turlarida mavzular bo‘sh bo‘lsa default diapazonni belgilab qo‘yish
        try:
            from quizzes.models import Theme
            if obj.type in (models.Exam.Type.MID_1, models.Exam.Type.MID_2, models.Exam.Type.MID_3) and obj.topics.count() == 0:
                if obj.type == models.Exam.Type.MID_1:
                    themes = Theme.objects.filter(order__gte=1, order__lte=11)
                elif obj.type == models.Exam.Type.MID_2:
                    themes = Theme.objects.filter(order__gte=12, order__lte=22)
                else:
                    themes = Theme.objects.filter(order__gte=23, order__lte=29)
                if themes.exists():
                    obj.topics.add(*themes)
        except Exception:
            pass


class ExamAccessAdmin(admin.ModelAdmin):
    list_display = ['id', 'exam', 'user']
    list_filter = ['exam', 'user']
    search_fields = ['user__full_name', 'user__telegram_id', 'exam__title']
    autocomplete_fields = ['exam', 'user']


class ExamAttemptAdmin(admin.ModelAdmin):
    date_hierarchy = 'started_at'
    list_display = [
        'id', 'exam', 'user', 'started_at', 'finished_at',
        'correct_count', 'wrong_count', 'total_questions', 'spent_time'
    ]
    list_filter = ['exam', 'user']
    search_fields = ['user__full_name', 'user__telegram_id', 'exam__title']
    autocomplete_fields = ['exam', 'user']
    inlines = [AttemptQuestionInline]


# Safe registrations (reload-friendly)
for model, admin_cls in (
    (models.Exam, ExamAdmin),
    (models.ExamAccess, ExamAccessAdmin),
    (models.ExamAttempt, ExamAttemptAdmin),
):
    try:
        admin.site.register(model, admin_cls)
    except AlreadyRegistered:
        pass

