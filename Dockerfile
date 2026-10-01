FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh \
    && DJANGO_DEBUG=False python manage.py collectstatic --noinput

# Yüklənmiş PDF-lər üçün daimi qovluq
RUN mkdir -p /data/media
ENV DJANGO_MEDIA_ROOT=/data/media
VOLUME /data/media

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
