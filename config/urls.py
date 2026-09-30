import re

from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import path, re_path
from django.views.static import serve

from core import views
from core.admin_site import command_center
from core.sitemaps import sitemaps


def robots_txt(request):
    admin_path = settings.ADMIN_URL_PATH
    body = f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /{admin_path}/\nSitemap: {settings.SITE_URL}/sitemap.xml\n"
    return HttpResponse(body, content_type="text/plain")


admin_path = settings.ADMIN_URL_PATH

urlpatterns = [
    path(f"{admin_path}/", command_center.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django-sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("projects/", views.projects, name="projects"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
    path("services/", views.services, name="services"),
    path("blog/", views.blog, name="blog"),
    path("blog/<slug:slug>/", views.post_detail, name="post_detail"),
    path("page/<slug:slug>/", views.page, name="page"),
    path("legal/<slug:slug>/", views.legal, name="legal"),
    path("contact/", views.contact, name="contact"),
    path("appointment/", views.appointment, name="appointment"),
    path("newsletter/", views.newsletter, name="newsletter"),
    path("cv/", views.download_cv, name="download_cv"),
    path("analytics/track/", views.track, name="track"),
    path("api/ai/chat/", views.ai_chat, name="ai_chat"),
]

urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
]
