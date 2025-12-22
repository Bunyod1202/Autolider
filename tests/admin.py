from django.contrib import admin
from django.contrib import messages
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
    # Avoid admin.E039 by not requiring Option admin; use raw_id_fields
    raw_id_fields = ['question', 'user_answer']


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
    actions = ["apply_default_topics_action"]

    def _select_default_topics(self, exam):
        from quizzes.models import Theme
        if exam.type not in (models.Exam.Type.MID_1, models.Exam.Type.MID_2, models.Exam.Type.MID_3):
            return 0
        if exam.topics.count() > 0:
            return 0
        if exam.type == models.Exam.Type.MID_1:
            a, b = 1, 11
        elif exam.type == models.Exam.Type.MID_2:
            a, b = 12, 22
        else:
            a, b = 23, 29
        selected = list(Theme.objects.filter(is_active=True, order__gte=a, order__lte=b))
        if not selected:
            active = list(Theme.objects.filter(is_active=True).order_by('order', 'id'))
            selected = [t for i, t in enumerate(active, start=1) if a <= i <= b]
        if selected:
            exam.topics.add(*selected)
            return len(selected)
        return 0

    @admin.action(description="Default mavzularni qo'llash (MID uchun)")
    def apply_default_topics_action(self, request, queryset):
        updated = 0
        skipped = 0
        for exam in queryset:
            try:
                cnt = self._select_default_topics(exam)
                if cnt:
                    updated += 1
                else:
                    skipped += 1
            except Exception:
                skipped += 1
        if updated:
            messages.success(request, f"Default mavzular qo'llandi: {updated} ta imtihon.")
        if skipped:
            messages.info(request, f"O'tkazib yuborildi (mavzular bor yoki FINAL): {skipped} ta.")

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

        # Fallback: agar yuqorida order diapazoni bo'yicha topilmasa va topics hamon bo'sh bo'lsa,
        # aktiv temalarni (order, id) bo'yicha ketma-ketlikda kesib tanlaymiz.
        try:
            from quizzes.models import Theme
            if obj.topics.count() == 0 and obj.type in (models.Exam.Type.MID_1, models.Exam.Type.MID_2, models.Exam.Type.MID_3):
                if obj.type == models.Exam.Type.MID_1:
                    a, b = 1, 11
                elif obj.type == models.Exam.Type.MID_2:
                    a, b = 12, 22
                else:
                    a, b = 23, 29
                active = list(Theme.objects.filter(is_active=True).order_by('order', 'id'))
                selected = [t for i, t in enumerate(active, start=1) if a <= i <= b]
                if selected:
                    obj.topics.add(*selected)
        except Exception:
            pass


class ExamAccessAdmin(admin.ModelAdmin):
    list_display = ['id', 'exam', 'user', 'max_attempts']
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

