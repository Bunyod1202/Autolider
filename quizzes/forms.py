from django import forms

from .models import Quiz


class DragAndDropFileInput(forms.ClearableFileInput):
    template_name = 'quizzes/widgets/dragndrop_file_input.html'


class QuizAdminForm(forms.ModelForm):
    image_upload = forms.ImageField(
        required=False,
        widget=DragAndDropFileInput,
        help_text=(
            "Rasmni tortib tashlang yoki tanlang. URL bo'lsa, pastdagi maydonga kiriting."
        ),
        label="Rasm (drag & drop)",
    )

    class Meta:
        model = Quiz
        fields = ['theme', 'question_uz', 'question_ru', 'image_url', 'is_active']

