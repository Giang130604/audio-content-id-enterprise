FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/packages/audio_id

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY packages /app/packages
COPY apps /app/apps

RUN pip install --no-cache-dir -e ".[api,infra]"

EXPOSE 8000

CMD ["uvicorn", "apps.api.audio_content_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

