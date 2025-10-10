from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django import forms
from django.db.models import OuterRef, Subquery

from users import models
from subscriptions.models import Subscription, Tariff
from subscriptions.utils import refresh_user_active_status


class UserAdminForm(forms.ModelForm):
    activation_days = forms.IntegerField(
        required=False,
        min_value=0,
        initial=7,
        help_text="Faollashtirish kunlari. 0 = cheksiz (doimiy). Default: 7"
    )

    class Meta:
        model = models.User
        fields = '__all__'


class TextFilter(AutocompleteFilter):
    title = 'Text'
    field_name = 'text'


class UserFilter(AutocompleteFilter):
    title = 'User'
    field_name = 'user'


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
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
        'days_left',
        'expires_at',
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
    actions = ['recalculate_active_status']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Annotate latest active (unchecked) subscription expire time for sorting
        latest_expire_subq = Subscription.objects.filter(
            user=OuterRef('pk'), is_checked=False
        ).order_by('-expire_time').values('expire_time')[:1]
        return qs.annotate(latest_expire_time=Subquery(latest_expire_subq))

    @admin.display(description="remaining days", ordering='latest_expire_time')
    def days_left(self, obj: models.User):
        now = timezone.now()
        # Prefer annotated value to avoid extra queries and enable sorting
        expire_time = getattr(obj, 'latest_expire_time', None)
        if expire_time is None or expire_time < now:
            # Fallback to DB check only if needed
            sub = obj.subscriptions.filter(is_checked=False, expire_time__gte=now).order_by('-expire_time').first()
            if not sub:
                return 0
            expire_time = sub.expire_time
        delta = expire_time - now
        return max(0, delta.days)

    @admin.display(description='expire time', ordering='latest_expire_time')
    def expires_at(self, obj: models.User):
        now = timezone.now()
        expire_time = getattr(obj, 'latest_expire_time', None)
        if expire_time is None:
            sub = obj.subscriptions.filter(is_checked=False).order_by('-expire_time').first()
            if sub:
                expire_time = sub.expire_time
        if not expire_time:
            return '-'
        label = expire_time.strftime('%Y-%m-%d %H:%M')
        if expire_time < now:
            # If expired but user still active, try to resync status now
            if obj.is_active:
                refresh_user_active_status(obj)
            # Show expired dates in red
            return format_html('<span style="color:#d00;">{} (expired)</span>', label)
        return label

    def save_model(self, request, obj: models.User, form, change):
        prev_is_active = None
        if change:
            try:
                prev_is_active = models.User.objects.get(pk=obj.pk).is_active
            except models.User.DoesNotExist:
                prev_is_active = None

        super().save_model(request, obj, form, change)

        now = timezone.now()
        # If just activated and no active subscription exists, create one with given days
        just_activated = (prev_is_active is False) and obj.is_active
        has_active_sub = obj.subscriptions.filter(is_checked=False, expire_time__gte=now).exists()

        if just_activated and not has_active_sub:
            days = form.cleaned_data.get('activation_days')
            if days is None:
                days = 7
            name_uz = f"Admin {'cheksiz' if days == 0 else days} kun"
            name_ru = f"Admin {'бессрочно' if days == 0 else days} дней"
            tariff, created = Tariff.objects.get_or_create(
                name_uz=name_uz,
                defaults={
                    'name_ru': name_ru,
                    'days': days,
                    'price': 0,
                    'is_active': True,
                }
            )
            if not created and tariff.days != days:
                tariff.days = days
                tariff.save(update_fields=['days'])

            # Determine expire_time: 0 means indefinite -> far future (100 years)
            if days == 0:
                expire_time = now + timezone.timedelta(days=365*100)
            else:
                expire_time = now + timezone.timedelta(days=days)

            Subscription.objects.create(
                user=obj,
                tariff=tariff,
                expire_time=expire_time,
            )

        # If admin deactivated the user, mark all current active subs as checked
        if change and (prev_is_active is True) and (obj.is_active is False):
            obj.subscriptions.filter(is_checked=False, expire_time__gte=now).update(is_checked=True)

    def recalculate_active_status(self, request, queryset):
        updated = 0
        for user in queryset:
            if refresh_user_active_status(user):
                updated += 1
        self.message_user(request, f"{queryset.count()} ta foydalanuvchi tekshirildi, {updated} ta yangilandi.")
    recalculate_active_status.short_description = 'Recalculate is_active by subscriptions'


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
