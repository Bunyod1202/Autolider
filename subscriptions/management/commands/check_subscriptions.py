from django.core.management.base import BaseCommand
from django.utils import timezone

from subscriptions.models import Subscription
from subscriptions.utils import refresh_user_active_status
from users.models import User


class Command(BaseCommand):
    help = (
        "Tugagan obunalarni tekshiradi va foydalanuvchini is_active=False holatga o'tkazadi.\n"
        "Admin orqali berilgan muddat tugaganda ham avtomatik o'chadi."
    )

    def handle(self, *args, **options):
        now = timezone.now()

        # 1) Avval tugagan, hali tekshirilmagan obunalarni yopamiz
        expired = Subscription.objects.filter(is_checked=False, expire_time__lt=now)
        total_expired = expired.count()
        for sub in expired:
            sub.is_checked = True
            sub.save(update_fields=["is_checked"])

        # 2) Endi barcha tegishli foydalanuvchilar holatini sinxronlaymiz
        user_ids = Subscription.objects.values_list('user_id', flat=True).distinct()
        users = User.objects.filter(id__in=user_ids)
        deactivated = 0
        activated = 0
        for user in users:
            before = user.is_active
            changed = refresh_user_active_status(user)
            if changed:
                if before and not user.is_active:
                    deactivated += 1
                elif (not before) and user.is_active:
                    activated += 1

        self.stdout.write(self.style.SUCCESS(
            f"{total_expired} ta obuna yopildi. {deactivated} ta foydalanuvchi o'chirildi, {activated} ta yoqildi."
        ))
