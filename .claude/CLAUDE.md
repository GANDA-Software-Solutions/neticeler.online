# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django 4.2 site (project package `config`, single app `results`) where exam participants look up their PDF result by exam + "iş nömrəsi" (work number), and staff upload PDFs through the Django admin. UI text, model verbose names, and comments are in Azerbaijani (`LANGUAGE_CODE = 'az'`, `TIME_ZONE = 'Asia/Baku'`); keep new user-facing strings in Azerbaijani. Source files are UTF-8 — if text looks garbled (`SÄ±naq`) it's a console encoding artifact, not file corruption.

## Commands

The app runs in Docker; prefer these commands over a local Python environment.

```
export DJANGO_SECRET_KEY=... POSTGRES_PASSWORD=...        # both required by docker-compose.yml (PowerShell: $env:NAME="...")
docker compose up --build -d                              # build + start on http://localhost:8000 (migrations run on start)
docker compose logs -f web
docker compose exec web python manage.py createsuperuser  # needed to use /admin/
docker compose exec web python manage.py test             # results/tests.py is currently empty
docker compose exec web python manage.py test results.tests.SomeTest.test_name   # single test
docker compose exec db psql -U results -d results         # inspect the database
docker compose down                                       # stop (volumes kept); add -v to wipe DB + PDFs
```

The database is PostgreSQL 16 (service `db`). Without Docker you need a reachable Postgres configured via the `POSTGRES_*` env vars (defaults: db/user/password `results`, host `localhost`, port 5432), then `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py runserver 8000` (also in `.claude/launch.json`). `media/` is gitignored locally. Legacy `db.sqlite3` is no longer used.

## Docker

- `Dockerfile`: `python:3.12-slim`, installs `requirements.txt` (includes `psycopg[binary]`), runs `collectstatic`, serves with `gunicorn config.wsgi` on port 8000. `docker-entrypoint.sh` runs `migrate --noinput` before starting (must keep LF line endings — enforced by `.gitattributes`), which creates the whole schema from `results/migrations/` on an empty database.
- `docker-compose.yml`: `db` (postgres:16-alpine, healthcheck, volume `pg_data`) and `web` (waits for `db` to be healthy; volume `media_data` at `/data/media` holds uploaded PDFs). Don't bake data into the image — `.dockerignore` excludes `db.sqlite3` and `media/`.
- Moving old SQLite data: with the old settings, `python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.permission -o data.json`, then in Docker `loaddata data.json` and copy the PDFs into the `media_data` volume.
- Static files (admin + `admin_theme.css`) are served by WhiteNoise from `STATIC_ROOT` (`staticfiles/`); re-run `collectstatic` (i.e. rebuild the image) after changing static files. PDFs are served by the app views (`bax/`, `yukle/`), not by `/media/` (that route exists only when `DEBUG=True`).
- Settings are env-driven: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (compose sets `False`), `DJANGO_ALLOWED_HOSTS` (comma-separated; default `localhost,127.0.0.1` in compose), `DJANGO_CSRF_TRUSTED_ORIGINS` (set to `https://your.domain` behind a TLS proxy, needed for admin login), `POSTGRES_DB`/`USER`/`PASSWORD`/`HOST`/`PORT` (compose sets host to `db`), `DJANGO_MEDIA_ROOT`.

## Architecture

- **Models** (`results/models.py`): `Exam` (name + date, auto-generated unique `slug`) and `ExamResult` (FK to exam, `work_number`, `pdf_file`). `ExamResult.save()` strips/uppercases `work_number`, and `(exam, work_number)` is unique. PDFs are stored at `media/results/<exam.slug>/<work_number>.pdf` via `result_upload_path` — the filename is derived from the work number, not the uploaded name.
- **Work number comes from the filename**: in admin, the work number is never typed on create; it's the uploaded file's basename without extension (`AZ12345.pdf` → `AZ12345`). On edit, `exam`/`work_number` are read-only, and replacing the file re-derives `work_number` from the new filename.
- **Duplicate handling = merge, not overwrite** (`results/utils.py: save_or_merge_result`): if a result already exists for the same exam + work number (different students sharing a number), the new PDF is appended to the existing one with `pypdf` and the old file is deleted/replaced. Both single admin upload (`ExamResultAdmin.save_model`) and bulk upload must go through this helper and return `"created"` / `"merged"`.
- **Admin** (`results/admin.py`): `ExamResultAdmin` adds a custom `bulk-upload/` URL (`results_examresult_bulk_upload`) using `BulkUploadForm` (a multi-file `MultipleFileField` in `forms.py`), rendered by `results/templates/admin/results/examresult/bulk_upload.html`; `change_list.html` adds the link. Admin styling lives in `results/static/results/css/admin_theme.css` and `templates/admin/base_site.html`.
- **Public views** (`results/views.py`, `results/urls.py`, mounted in `config/urls.py`): `home` (GET search via `SearchForm`; `searched` flag is `"work_number" in request.GET`), `download_result` (`yukle/<pk>/`, attachment) and `view_result` (`bax/<pk>/`, inline, `xframe_options_sameorigin` so `home.html` can embed it in an iframe). These are keyed by integer pk and unauthenticated.
- **Settings** (`config/settings.py`): project-level templates dir is `templates/`; `MEDIA_URL = '/media/'`. `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, Postgres connection and `MEDIA_ROOT` are read from env vars (see Docker section); the fallback defaults (hard-coded key, `DEBUG=True`) are for local dev only. WhiteNoise middleware serves static files.

## Gotchas

- `results_onsite/` inside the repo root contains only a `.gitattributes`; it is not a Python package.
- Migrations are in `results/migrations/` (0001–0004); `Exam` and its `slug` were added after the initial migration.
