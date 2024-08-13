#!/bin/ash

echo "Applying database migrations"
python manage.py migrate

exec "$@"