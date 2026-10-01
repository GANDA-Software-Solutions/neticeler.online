# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django 4.2 site (project package `config`, single app `results`) where exam participants look up their PDF result by exam + "iş nömrəsi" (work number), and staff upload PDFs through the Django admin. UI text, model verbose names, and comments are in Azerbaijani (`LANGUAGE_CODE = 'az'`, `TIME_ZONE = 'Asia/Baku'`); keep new user-facing strings in Azerbaijani. Source files are UTF-8 — if text looks garbled (`SÄ±naq`) it's a console encoding artifact, not file corruption.

## Commands

```
pip install -r requirements.txt        # Django, pypdf
python manage.py migrate
python manage.py createsuperuser       # needed to use /admin/
python manage.py runserver 8000        # also configured in .claude/launch.json
python manage.py test                  # results/tests.py is currently empty
python manage.py test results.tests.SomeTest.test_name   # single test
```

SQLite (`db.sqlite3`) is the database; it and `media/` are gitignored. The project directory is not currently a git repo.

## Architecture

- **Models** (`results/models.py`): `Exam` (name + date, auto-generated unique `slug`) and `ExamResult` (FK to exam, `work_number`, `pdf_file`). `ExamResult.save()` strips/uppercases `work_number`, and `(exam, work_number)` is unique. PDFs are stored at `media/results/<exam.slug>/<work_number>.pdf` via `result_upload_path` — the filename is derived from the work number, not the uploaded name.
- **Work number comes from the filename**: in admin, the work number is never typed on create; it's the uploaded file's basename without extension (`AZ12345.pdf` → `AZ12345`). On edit, `exam`/`work_number` are read-only, and replacing the file re-derives `work_number` from the new filename.
- **Duplicate handling = merge, not overwrite** (`results/utils.py: save_or_merge_result`): if a result already exists for the same exam + work number (different students sharing a number), the new PDF is appended to the existing one with `pypdf` and the old file is deleted/replaced. Both single admin upload (`ExamResultAdmin.save_model`) and bulk upload must go through this helper and return `"created"` / `"merged"`.
- **Admin** (`results/admin.py`): `ExamResultAdmin` adds a custom `bulk-upload/` URL (`results_examresult_bulk_upload`) using `BulkUploadForm` (a multi-file `MultipleFileField` in `forms.py`), rendered by `results/templates/admin/results/examresult/bulk_upload.html`; `change_list.html` adds the link. Admin styling lives in `results/static/results/css/admin_theme.css` and `templates/admin/base_site.html`.
- **Public views** (`results/views.py`, `results/urls.py`, mounted in `config/urls.py`): `home` (GET search via `SearchForm`; `searched` flag is `"work_number" in request.GET`), `download_result` (`yukle/<pk>/`, attachment) and `view_result` (`bax/<pk>/`, inline, `xframe_options_sameorigin` so `home.html` can embed it in an iframe). These are keyed by integer pk and unauthenticated.
- **Settings** (`config/settings.py`): project-level templates dir is `templates/`; `MEDIA_ROOT = BASE_DIR / 'media'`, `MEDIA_URL = '/media/'`. `DEBUG = True`, empty `ALLOWED_HOSTS`, and a hard-coded `SECRET_KEY` — dev configuration, not production-ready.

## Gotchas

- `results_onsite/` inside the repo root contains only a `.gitattributes`; it is not a Python package.
- Migrations are in `results/migrations/` (0001–0004); `Exam` and its `slug` were added after the initial migration.
