import os
from io import BytesIO

from django.core.files.base import ContentFile
from pypdf import PdfWriter


def merge_pdfs(*file_sources) -> bytes:
    """Bir neçə PDF faylını (fayl-obyekt və ya bytes) səhifə-səhifə birləşdirib
    nəticəni bytes olaraq qaytarır."""
    writer = PdfWriter()
    for source in file_sources:
        if hasattr(source, "read"):
            source.seek(0)
            data = source.read()
        else:
            data = source
        writer.append(BytesIO(data))

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def save_or_merge_result(exam, work_number, uploaded_file):
    """(sınaq, iş nömrəsi) üzrə nəticəni yaradır. Əgər bu sınaqda həmin iş
    nömrəsi ilə nəticə artıq mövcuddursa (fərqli şagirdlər eyni nömrəni
    yazıbsa), yeni faylı üzərinə yazmaq əvəzinə hər iki PDF-i tək sənəddə
    birləşdirir ki, axtarışda hər ikisi görünsün."""
    from .models import ExamResult

    work_number = work_number.strip().upper()
    existing = ExamResult.objects.filter(exam=exam, work_number=work_number).first()

    if existing is None:
        obj = ExamResult(exam=exam, work_number=work_number)
        obj.pdf_file.save(uploaded_file.name, uploaded_file, save=True)
        return obj, "created"

    existing.pdf_file.open("rb")
    try:
        existing_bytes = existing.pdf_file.read()
    finally:
        existing.pdf_file.close()

    merged_bytes = merge_pdfs(existing_bytes, uploaded_file)
    old_name = existing.pdf_file.name
    existing.pdf_file.storage.delete(old_name)
    existing.pdf_file.save(os.path.basename(old_name), ContentFile(merged_bytes), save=True)
    return existing, "merged"
