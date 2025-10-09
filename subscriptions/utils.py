from django.utils import timezone

from .models import Subscription


def refresh_user_active_status(user) -> bool:
    """Synchronize a user's `is_active` with their subscriptions.

    Steps:
    1️⃣ Mark expired and unchecked subscriptions as checked.
    2️⃣ Check if any active subscription exists (is_checked=False and expire_time >= now).
    3️⃣ If user's `is_active` changed, save with update_fields=["is_active"].

    Returns True if the user's active status changed, otherwise False.
    """

    now = timezone.now()

    # 1️⃣ Mark all expired, unchecked subscriptions as checked
    expired_qs = Subscription.objects.filter(
        user=user,
        is_checked=False,
        expire_time__lt=now,
    )
    if expired_qs.exists():
        expired_qs.update(is_checked=True)

    # 2️⃣ Determine whether the user currently has any active subscription
    has_active = Subscription.objects.filter(
        user=user,
        is_checked=False,
        expire_time__gte=now,
    ).exists()

    # 3️⃣ Update the user if the active state changed
    if user.is_active != has_active:
        user.is_active = has_active
        user.save(update_fields=["is_active"])  # persist only the changed field
        return True

    return False

