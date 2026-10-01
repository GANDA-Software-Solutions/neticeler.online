from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import SearchForm
from .models import ExamResult


def home(request):
    searched = "work_number" in request.GET
    form = SearchForm(request.GET or None)
    result = None

    if searched and form.is_valid():
        exam = form.cleaned_data["exam"]
        work_number = form.cleaned_data["work_number"].strip().upper()
        result = ExamResult.objects.filter(exam=exam, work_number=work_number).first()

    return render(
        request,
        "results/home.html",
        {"form": form, "result": result, "searched": searched},
    )


def download_result(request, pk):
    result = get_object_or_404(ExamResult, pk=pk)
    return FileResponse(
        result.pdf_file.open("rb"),
        as_attachment=True,
        filename=f"{result.work_number}.pdf",
    )


@xframe_options_sameorigin
def view_result(request, pk):
    result = get_object_or_404(ExamResult, pk=pk)
    return FileResponse(
        result.pdf_file.open("rb"),
        as_attachment=False,
        filename=f"{result.work_number}.pdf",
    )
