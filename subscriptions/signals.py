from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Subscription
from .utils import refresh_user_active_status


@receiver(post_save, sender=Subscription)
def subscription_saved(sender, instance: Subscription, **kwargs):
    # Whenever a subscription is saved via admin/UI, recalculate user's active status
    refresh_user_active_status(instance.user)


@receiver(post_delete, sender=Subscription)
def subscription_deleted(sender, instance: Subscription, **kwargs):
    # If a subscription is deleted, recompute status as well
    refresh_user_active_status(instance.user)

