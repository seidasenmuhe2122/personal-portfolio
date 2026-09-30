#!/usr/bin/env bash
set -o errexit
python manage.py migrate --noinput
python manage.py site_seed
python manage.py collectstatic --noinput
