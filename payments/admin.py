from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from threading import Timer

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
        'auto_deactivate_after_2m',
        'added_time',
        'last_updated_time',
    ]
    list_filter = [
        'is_active',
        'auto_deactivate_after_2m',
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

    fields = [
        'name_uz', 'name_ru', 'data',
        'is_active', 'auto_deactivate_after_2m',
        'added_time', 'last_updated_time',
    ]

    def save_model(self, request, obj, form, change):
        # Set/deactivate due timestamp according to checkbox
        if form.cleaned_data.get('auto_deactivate_after_2m'):
            obj.auto_deactivate_due = timezone.now() + timedelta(minutes=2)
        else:
            obj.auto_deactivate_due = None

        super().save_model(request, obj, form, change)

        # If auto-deactivate enabled, schedule a one-shot timer in-process
        if obj.auto_deactivate_after_2m and obj.auto_deactivate_due:
            delay = (obj.auto_deactivate_due - timezone.now()).total_seconds()
            delay = max(0, min(delay, 2*60))

            def _deactivate(pk):
                from payments.models import Provider
                try:
                    p = Provider.objects.get(pk=pk)
                except Provider.DoesNotExist:
                    return
                # Only deactivate if still requested and due time reached/passed
                if p.auto_deactivate_after_2m and p.auto_deactivate_due and timezone.now() >= p.auto_deactivate_due:
                    p.is_active = False
                    # Optionally clear the flag so it doesn't run again
                    p.auto_deactivate_after_2m = False
                    p.auto_deactivate_due = None
                    p.save(update_fields=['is_active', 'auto_deactivate_after_2m', 'auto_deactivate_due', 'last_updated_time'])

            try:
                Timer(delay, _deactivate, args=(obj.pk,)).start()
            except Exception:
                # If timer can't be scheduled, silently ignore; admin can toggle manually
                pass


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
