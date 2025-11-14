from django import forms

from .models import Quiz


class QuizAdminForm(forms.ModelForm):
    image_upload = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        help_text=(
            "Rasmni tanlang yoki tashlang — avtomatik serverga yuklanadi va image_url to'ldiriladi."
        ),
        label="Rasm",
    )

    class Meta:
        model = Quiz
        fields = ['theme', 'question_uz', 'question_ru', 'image_url', 'is_active']

    class Media:
        js = (
            'admin/quiz_dnd.js',
        )
