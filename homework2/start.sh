#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/movie_theater_booking"
# Free Render services have no pre-deploy command. Run migrations before Gunicorn.
python manage.py migrate --noinput
python manage.py seed_demo
exec gunicorn movie_theater_booking.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --access-logfile -
