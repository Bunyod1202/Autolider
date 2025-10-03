from django.db import models


class Test(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='tests',
    )
    theme = models.ForeignKey(
        'quizzes.Theme',
        on_delete=models.CASCADE,
        related_name='tests',
    )
    quizzes_count = models.PositiveSmallIntegerField()
    correct_answers_count = models.PositiveSmallIntegerField()
    spent_seconds = models.PositiveIntegerField()
    selected_options = models.ManyToManyField(
        'quizzes.Option',
        related_name='tests',
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
    )
    last_updated_time = models.DateTimeField(
        auto_now=True,
    )

    @property
    def spent_time(self):
        hours = self.spent_seconds // 3600
        minutes = self.spent_seconds % 3600 // 60
        seconds = self.spent_seconds % 3600 % 60
        raw = ""
        if hours:
            raw += self.user.text.left_hours.format(
                hours=hours,
            ) + " "
        if minutes:
            raw += self.user.text.left_minutes.format(
                minutes=minutes,
            ) + " "
        if seconds:
            raw += self.user.text.left_seconds.format(
                seconds=seconds,
            ) + " "
        raw += self.user.text.left
        return raw

    @property
    def correct_answers(self):
        return self.user.text.correct_answers_info.format(
            correct_answers_count=self.correct_answers_count,
            quizzes_count=self.quizzes_count,
            percentage=round(self.correct_answers_count*100/self.quizzes_count, 2),
        )

    def __str__(self):
        return f"{self.user}'s ID{self.id} test: {self.correct_answers_count}/{self.quizzes_count} in {self.spent_seconds} seconds."
