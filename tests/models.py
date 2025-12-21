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


class Exam(models.Model):
    class Type(models.TextChoices):
        MID_1 = 'MID_1', 'Oraliq imtihon 1'
        MID_2 = 'MID_2', 'Oraliq imtihon 2'
        MID_3 = 'MID_3', 'Oraliq imtihon 3'
        FINAL = 'FINAL', 'Yakuniy imtihon'

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=8, choices=Type.choices)
    date = models.DateTimeField()
    question_count = models.PositiveSmallIntegerField(default=20)
    topics = models.ManyToManyField(
        'quizzes.Theme', blank=True, related_name='exams'
    )
    allowed_users = models.ManyToManyField(
        'users.User', through='tests.ExamAccess', related_name='allowed_exams', blank=True
    )
    is_active = models.BooleanField(default=True)
    added_time = models.DateTimeField(auto_now_add=True)
    last_updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"

    class Meta:
        verbose_name = 'Imtihon'
        verbose_name_plural = 'Imtihonlar'


class ExamAccess(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='accesses')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='exam_accesses')

    class Meta:
        unique_together = ('exam', 'user')

    def __str__(self):
        return f"{self.user} → {self.exam}"

    class Meta:
        verbose_name = 'Imtihon ruxsati'
        verbose_name_plural = 'Imtihon ruxsatlari'


class ExamAttempt(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='exam_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    correct_count = models.PositiveSmallIntegerField(default=0)
    wrong_count = models.PositiveSmallIntegerField(default=0)
    total_questions = models.PositiveSmallIntegerField(default=0)
    spent_time = models.PositiveIntegerField(default=0)  # seconds

    def __str__(self):
        return f"Attempt #{self.id} by {self.user} for {self.exam}"

    class Meta:
        verbose_name = 'Imtihon urinish'
        verbose_name_plural = 'Imtihon urinishlari'


class AttemptQuestion(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='attempt_questions')
    question = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    user_answer = models.ForeignKey('quizzes.Option', null=True, blank=True, on_delete=models.SET_NULL)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('attempt', 'question')
        ordering = ['order']
        verbose_name = 'Urinish savoli'
        verbose_name_plural = 'Urinish savollari'

    def __str__(self):
        return f"Attempt {self.attempt_id} Q{self.order}: {self.question_id}"
