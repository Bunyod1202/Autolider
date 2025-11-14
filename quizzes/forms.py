from django import forms

from .models import Quiz


class DragAndDropFileInput(forms.ClearableFileInput):
    template_name = 'quizzes/widgets/dragndrop_file_input.html'

    def get_context(self, name, value, attrs):
        attrs = attrs or {}
        attrs.setdefault('id', f'id_{name}')
        return super().get_context(name, value, attrs)


class QuizAdminForm(forms.ModelForm):
    image_upload = forms.ImageField(
        required=False,
        widget=DragAndDropFileInput(attrs={'accept': 'image/*'}),
        help_text=(
            "Rasmni tortib tashlang yoki tanlang — avtomatik serverga yuklanadi va image_url to'ldiriladi."
        ),
        label="Rasm (drag & drop)",
    )

    class Meta:
        model = Quiz
        fields = ['theme', 'question_uz', 'question_ru', 'image_url', 'is_active']
