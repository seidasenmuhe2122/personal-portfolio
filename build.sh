#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py site_seed
python manage.py create_render_admin
python manage.py collectstatic --noinput