FROM python:3.8-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && pip install --no-cache-dir gunicorn psycopg2-binary
COPY . /app
RUN python - <<'PY' || true
import os, subprocess
os.environ.setdefault('DJANGO_SETTINGS_MODULE','avtolider_bot.settings')
subprocess.run(['python','manage.py','collectstatic','--noinput'], check=False)
PY
EXPOSE 8000
CMD ["gunicorn","--bind","0.0.0.0:8000","--workers","3","avtolider_bot.wsgi:application"]
