# syntax=docker/dockerfile:1

FROM node:24-alpine AS frontend-build

WORKDIR /app

COPY package.json package-lock.json tailwind.config.js ./
RUN npm ci

COPY src/frontend/assets ./src/frontend/assets
COPY src/frontend/templates ./src/frontend/templates
RUN npm run css:build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/src/backend \
    PORT=8000

WORKDIR /app

COPY src/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .
COPY --from=frontend-build \
    /app/src/frontend/static/css/index.css \
    /app/src/frontend/static/css/index.css

RUN useradd --create-home --shell /usr/sbin/nologin chipbuddy \
    && mkdir -p /app/data/runtime \
    && chown -R chipbuddy:chipbuddy /app/data/runtime

USER chipbuddy

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=3)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
