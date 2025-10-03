import uuid

from django.db import models

from bot.utils.constants import USER


class User(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    telegram_id = models.CharField(
        max_length=31,
        unique=True
    )
    full_name = models.CharField(
        max_length=255
    )
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
    )
    username = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    text = models.ForeignKey(
        'bot.Text',
        on_delete=models.SET_NULL,
        related_name='users',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=False
    )
    is_admin = models.BooleanField(
        default=False
    )
    step = models.CharField(
        max_length=7,
        default=USER.STEP.MAIN
    )
    data = models.TextField(
        null=True,
        blank=True
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    def set_step(self, step: str = USER.STEP.MAIN, data=None):
        self.step = step
        self.data = data
        self.save()

    def check_step(self, step: str):
        return step == self.step

    def __str__(self):
        return self.full_name


class Log(models.Model):
    user = models.ForeignKey(
        User,
        models.CASCADE,
        related_name='logs'
    )
    reason = models.CharField(
        max_length=15,
        choices=USER.LOG.TYPE.CHOICES
    )
    text = models.TextField()
    added_time = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.id} {USER.LOG.TYPE.DICT.get(self.reason)}"
