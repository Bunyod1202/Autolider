#!/usr/bin/env sh
set -e

python manage.py migrate --noinput
# Static collection is also done at build time, but repeat safely at start
python manage.py collectstatic --noinput || true

exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${WORKERS:-3} avtolider_bot.wsgi:application

