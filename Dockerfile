# Tenable Report Analyser - Django app
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install netcat for entrypoint wait
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ .

# Create static directory (avoids STATICFILES_DIRS warning if missing)
RUN mkdir -p static

# Entrypoint created inside image (Unix line endings, no CRLF)
RUN printf '%s\n' \
  '#!/bin/sh' \
  'set -e' \
  'POSTGRES_HOST="${POSTGRES_HOST:-db}"' \
  'POSTGRES_PORT="${POSTGRES_PORT:-5432}"' \
  'echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."' \
  'while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT" 2>/dev/null; do sleep 1; done' \
  'echo "PostgreSQL is up."' \
  'python manage.py migrate --noinput' \
  'python manage.py collectstatic --noinput --clear 2>/dev/null || true' \
  'exec "$@"' \
  > /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "tenable_web.wsgi:application"]
