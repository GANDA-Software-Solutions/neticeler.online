from django import forms

from .models import Exam


class SearchForm(forms.Form):
    exam = forms.ModelChoiceField(
        label="Sınaq tarixi",
        queryset=Exam.objects.all(),
        empty_label="Sınaq seçin",
    )
    work_number = forms.CharField(
        label="İş nömrəsi",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "placeholder": "İş nömrənizi daxil edin",
            }
        ),
    )


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class BulkUploadForm(forms.Form):
    exam = forms.ModelChoiceField(
        label="Sınaq",
        queryset=Exam.objects.all(),
        empty_label="Sınaq seçin",
    )
    pdf_files = MultipleFileField(
        label="PDF faylları",
        help_text=(
            "Bir və ya bir neçə PDF faylı seçin. Hər faylın adı iş nömrəsi "
            "olmalıdır (məs. AZ12345.pdf). Eyni sınaqda eyni iş nömrəsi ilə "
            "fayl artıq mövcuddursa, yeni fayl əvvəlkinin üzərinə yazılmır — "
            "hər iki PDF bir sənəddə birləşdirilir."
        ),
    )
