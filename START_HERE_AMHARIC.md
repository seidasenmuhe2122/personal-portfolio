# SEID DIGITAL PLATFORM — FINAL PACKAGE

ይህ የproject የመጨረሻ ስሪት ነው። ከዚህ በኋላ CSS/template/admin ፋይሎችን በእጅ መቀየር አያስፈልግም።

## 1. አሁን ያለው project ከሆነ
ZIP ፋይሉን አንድ ጊዜ extract አድርግ። `INSTALL_FINAL.ps1` ላይ Right click → Run with PowerShell አድርግ።

Installer-ው `C:\digital\platform` ን ይጠቀማል፣ `db.sqlite3`, `media`, `.env` እና Git ን አያጠፋም። ከመቀየሩ በፊት backup ይፈጥራል።

## 2. በእጅ ማስኬድ ከፈለግህ
```powershell
cd C:\digital\platform
.\venv\Scripts\Activate.ps1
$env:DEBUG = 'True'
python manage.py migrate
python manage.py site_seed
python manage.py collectstatic --noinput
python manage.py runserver
```

## 3. Admin
- የAdmin መንገድ በ`ADMIN_URL_PATH` environment variable ይወሰናል።
- `/admin/` መንገድ አይጠቀምም።

ያለው superuser አይጠፋም።

## 4. የተካተቱ ነገሮች
- Premium responsive portfolio
- Dark / light mode
- Projects, services, skills, experience, education, certificates
- Blog/CMS: draft, review, scheduled, published, archived
- Pages + custom sections + legal pages
- Media library
- Contact inbox
- Appointment requests
- Newsletter
- CV download tracking
- AI assistant + Gemini API support
- Analytics
- GitHub sync
- Telegram publishing
- Webhooks/integrations models
- Automation/scheduled publishing commands
- Backup command
- SEO meta + Open Graph
- Sitemap + robots.txt
- Maintenance mode
- Custom Command Center admin
- Users/groups/permissions
- Activity/audit log models
- Social links with real platform logos/icons
- Mobile navigation and accessibility
- Production PostgreSQL support through `DATABASE_URL`
- Render deployment files

## 5. API keys / integrations
External services cannot be activated without their own credentials. Put credentials in Render Environment Variables or a local `.env`; never put secrets inside Python code.

Important variables are listed in `.env.example`:
- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `GEMINI_API_KEY`
- `GITHUB_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- SMTP variables

## 6. Render
The package already contains `render.yaml` and `build.sh`. Connect the project repository to Render and use the Blueprint configuration. Set your public `SITE_URL`, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for the final domain.

## 7. Data safety
አሮጌ `db.sqlite3` አትሰርዝ። Installer-ው ራሱ backup ይፈጥራል። Production ላይ PostgreSQL መጠቀም ይመከራል።
