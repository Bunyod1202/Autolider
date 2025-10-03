from django.db import models

from bot.utils.constants import LANGUAGE


class Theme(models.Model):
    name_uz = models.CharField(
        max_length=63,
        unique=True,
    )
    name_ru = models.CharField(
        max_length=63,
        unique=True,
    )
    order = models.PositiveSmallIntegerField(
        default=0,
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

    class Meta:
        ordering = ['order', ]


class Quiz(models.Model):
    theme = models.ForeignKey(
        Theme,
        on_delete=models.CASCADE,
        related_name='quizzes',
    )
    question_uz = models.TextField()
    question_ru = models.TextField()
    image_url = models.URLField(
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    def question(self, language: str):
        if language == LANGUAGE.UZ:
            return self.question_uz
        return self.question_ru

    def __str__(self):
        return self.question_uz


class Option(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='options',
    )
    text_uz = models.TextField()
    text_ru = models.TextField()
    is_correct = models.BooleanField(
        default=False,
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    def text(self, language: str):
        if language == LANGUAGE.UZ:
            return self.text_uz
        return self.text_ru

    def __str__(self):
        return f"{'✅' if self.is_correct else '❌'} {self.text_uz}"

    class Meta:
        ordering = ['id', ]


