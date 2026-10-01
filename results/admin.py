import os

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import BulkUploadForm
from .models import Exam, ExamResult
from .utils import save_or_merge_result


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "result_count")
    search_fields = ("name",)
    ordering = ("-date",)

    def result_count(self, obj):
        return obj.results.count()

    result_count.short_description = "Nəticə sayı"


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("work_number", "exam", "uploaded_at", "view_pdf")
    list_filter = ("exam",)
    search_fields = ("work_number",)
    ordering = ("-uploaded_at",)
    change_list_template = "admin/results/examresult/change_list.html"

    def view_pdf(self, obj):
        return format_html('<a href="{}" target="_blank">Bax</a>', obj.pdf_file.url)

    view_pdf.short_description = "PDF"

    def get_fields(self, request, obj=None):
        if obj:
            return ("exam", "work_number", "pdf_file")
        return ("exam", "pdf_file")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("exam", "work_number")
        return ()

    def save_model(self, request, obj, form, change):
        if change:
            if "pdf_file" in form.changed_data:
                obj.work_number = os.path.splitext(os.path.basename(obj.pdf_file.name))[0]
            super().save_model(request, obj, form, change)
            return

        work_number = os.path.splitext(os.path.basename(obj.pdf_file.name))[0]
        result_obj, status = save_or_merge_result(obj.exam, work_number, obj.pdf_file)
        obj.pk = result_obj.pk
        obj.work_number = result_obj.work_number
        obj.pdf_file = result_obj.pdf_file
        obj.uploaded_at = result_obj.uploaded_at

        if status == "merged":
            messages.warning(
                request,
                f"'{result_obj.work_number}' iş nömrəsi ilə '{result_obj.exam}' sınağında "
                "artıq nəticə var idi — yeni fayl üzərinə yazılmadı, hər iki PDF bir sənəddə "
                "birləşdirildi.",
            )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "bulk-upload/",
                self.admin_site.admin_view(self.bulk_upload_view),
                name="results_examresult_bulk_upload",
            ),
        ]
        return custom_urls + urls

    def bulk_upload_view(self, request):
        if request.method == "POST":
            form = BulkUploadForm(request.POST, request.FILES)
            if form.is_valid():
                exam = form.cleaned_data["exam"]
                created, merged = 0, 0
                for f in form.cleaned_data["pdf_files"]:
                    work_number = os.path.splitext(os.path.basename(f.name))[0]
                    _, status = save_or_merge_result(exam, work_number, f)
                    if status == "created":
                        created += 1
                    else:
                        merged += 1

                message = f"{created} yeni nəticə əlavə edildi."
                if merged:
                    message += (
                        f" {merged} nəticə üçün eyni iş nömrəsi ilə fayl artıq mövcud idi — "
                        "PDF-lər bir sənəddə birləşdirildi."
                    )
                messages.success(request, message)
                return redirect(reverse("admin:results_examresult_changelist"))
        else:
            form = BulkUploadForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            title="PDF nəticələrini toplu əlavə et",
            opts=self.model._meta,
        )
        return render(request, "admin/results/examresult/bulk_upload.html", context)
