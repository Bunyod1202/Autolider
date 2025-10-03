from django.db import models

from bot.utils.constants import LANGUAGE


class Tariff(models.Model):
    name_uz = models.CharField(
        max_length=63,
        unique=True,
    )
    name_ru = models.CharField(
        max_length=63,
        unique=True,
    )
    days = models.PositiveSmallIntegerField()
    price = models.PositiveIntegerField()
    is_active = models.BooleanField(
        default=False,
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    def name(self, language: str):
        if language == LANGUAGE.UZ:
            return self.name_uz
        return self.name_ru

    def __str__(self):
        return self.name_uz


class Subscription(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    expire_time = models.DateTimeField()
    is_checked = models.BooleanField(
        default=False,
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user}'s ID{self.id} subscription until {self.expire_time}"
