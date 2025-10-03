from django.db import models

from bot.utils.constants import LANGUAGE


class Provider(models.Model):
    name_uz = models.CharField(
        max_length=63,
        unique=True,
    )
    name_ru = models.CharField(
        max_length=63,
        unique=True,
    )
    data = models.TextField(
        null=True,
        blank=True,
    )
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


class Payment(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='payments',
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    subscription = models.OneToOneField(
        'subscriptions.Subscription',
        on_delete=models.CASCADE,
        related_name='payment',
    )
    provider_transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    amount = models.PositiveIntegerField()
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user}'s {self.amount:,} payment for {self.subscription}"
