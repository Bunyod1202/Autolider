from django import forms

from .models import Quiz


class QuizAdminForm(forms.ModelForm):
    image_upload = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        help_text=(
            "Rasmni tanlang (yoki URL kiriting)."
        ),
        label="Rasm fayl",
    )

    class Meta:
        model = Quiz
        fields = ['theme', 'question_uz', 'question_ru', 'image_url', 'is_active']
