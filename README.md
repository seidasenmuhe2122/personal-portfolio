# Seid Digital Platform — Final Complete Build

A premium personal digital platform built with Django 6.1. It combines a public portfolio, CMS, AI assistant, analytics, appointments, newsletter, integrations, automation and a custom Command Center admin.

## What is included
- Premium responsive portfolio with dark/light mode
- Home, About, Projects, Services, Blog, Contact and Appointment flows
- Skills, experience, education, certificates and testimonials
- CMS posts with draft/review/scheduled/published/archived states
- Custom pages, sections and legal pages
- Media library
- Contact inbox and appointment requests
- Newsletter subscription endpoint
- CV download endpoint with analytics
- Gemini-powered AI assistant with fallback mode and basic rate limiting
- GitHub metadata sync command
- Telegram publishing command
- Scheduled content publishing command
- Database backup command
- Analytics event storage and activity log models
- Webhook/integration/automation configuration models
- SEO metadata, Open Graph, sitemap.xml and robots.txt
- Maintenance mode
- Custom premium Command Center at the deployment-specific `ADMIN_URL_PATH` (no `/admin/` alias)
- Users/groups/permissions inside the same admin
- Render + PostgreSQL deployment foundation

## Safety when upgrading
Do not delete `db.sqlite3`, `media/`, `.env` or your Git repository. The included `INSTALL_FINAL.ps1` creates a timestamped backup before copying the application files into `C:\digital\platform`.

## Local
```powershell
cd C:\digital\platform
.\venv\Scripts\Activate.ps1
$env:DEBUG = 'True'
python manage.py migrate
python manage.py site_seed
python manage.py collectstatic --noinput
python manage.py runserver
```

## Production
Use PostgreSQL through `DATABASE_URL`, set a strong `DJANGO_SECRET_KEY`, configure `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL`, email and optional integration credentials in the hosting environment. Set `REDIS_URL` to a shared Redis instance in production so rate limits are consistent across application workers and instances; local development falls back to Django's in-process cache.

The application code does not contain production secrets.
