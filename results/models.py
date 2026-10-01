from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify


class Exam(models.Model):
    name = models.CharField("Sınağın adı", max_length=200)
    date = models.DateField("Sınaq tarixi")
    slug = models.SlugField(max_length=220, unique=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Sınaq"
        verbose_name_plural = "Sınaqlar"
        ordering = ["-date", "name"]
        constraints = [
            models.UniqueConstraint(fields=["name", "date"], name="unique_exam_name_date"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.date}-{self.name}") or f"sinaq-{self.date}"
            slug = base
            counter = 2
            while Exam.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.date:%d.%m.%Y})"


def result_upload_path(instance, filename):
    return f"results/{instance.exam.slug}/{instance.work_number}.pdf"


class ExamResult(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name="Sınaq",
    )
    work_number = models.CharField(
        "İş nömrəsi",
        max_length=50,
        db_index=True,
        help_text="Sınaq iştirakçısının iş nömrəsi (məs. AZ12345)",
    )
    pdf_file = models.FileField(
        "PDF nəticə",
        upload_to=result_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )
    uploaded_at = models.DateTimeField("Yükləmə tarixi", auto_now_add=True)

    class Meta:
        verbose_name = "Sınaq nəticəsi"
        verbose_name_plural = "Sınaq nəticələri"
        ordering = ["-uploaded_at"]
        constraints = [
            models.UniqueConstraint(fields=["exam", "work_number"], name="unique_exam_work_number"),
        ]

    def save(self, *args, **kwargs):
        self.work_number = self.work_number.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.work_number} — {self.exam}"
