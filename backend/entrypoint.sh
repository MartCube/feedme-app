#!/bin/sh
# Dev bootstrap: migrate + ensure the env-driven superuser, then run the CMD.
set -e

python manage.py migrate
python manage.py ensure_superuser

exec "$@"
