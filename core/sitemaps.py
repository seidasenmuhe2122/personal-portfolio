from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Project, Post, Page, LegalPage


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["home", "about", "projects", "services", "blog", "contact", "appointment"]

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Project.objects.filter(published=True)

    def location(self, item):
        return reverse("project_detail", args=[item.slug])


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Post.objects.filter(status="published")

    def lastmod(self, item):
        return item.updated_at

    def location(self, item):
        return reverse("post_detail", args=[item.slug])


class PageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Page.objects.filter(published=True)

    def location(self, item):
        return reverse("page", args=[item.slug])


class LegalSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.2

    def items(self):
        return LegalPage.objects.filter(published=True)

    def location(self, item):
        return reverse("legal", args=[item.slug])


sitemaps = {
    "static": StaticViewSitemap,
    "projects": ProjectSitemap,
    "posts": PostSitemap,
    "pages": PageSitemap,
    "legal": LegalSitemap,
}
