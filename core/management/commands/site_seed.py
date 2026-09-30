from django.core.management.base import BaseCommand
from core.models import SiteSettings, Profile, LegalPage, Section, SocialLink


class Command(BaseCommand):
    help = "Create safe first-run content without overwriting existing records."

    def handle(self, *args, **kwargs):
        SiteSettings.objects.get_or_create(pk=1)
        Profile.objects.get_or_create(
            pk=1,
            defaults={
                "name": "Seid Asen Muhe",
                "headline": "Technology • Cybersecurity • AI • Automation",
                "bio": "Technology professional building secure, useful digital products.",
            },
        )
        legal = [
            ("Privacy Policy", "privacy-policy"),
            ("Terms of Service", "terms-of-service"),
            ("Cookie Policy", "cookie-policy"),
        ]
        for title, slug in legal:
            LegalPage.objects.get_or_create(
                slug=slug,
                defaults={"title": title, "content": f"<h2>{title}</h2><p>Edit this page from the Command Center.</p>"},
            )
        sections = [
            ("Hero", "hero"), ("About", "about"), ("Skills", "skills"), ("Projects", "projects"),
            ("Services", "services"), ("Experience", "experience"), ("Education", "education"),
            ("Certificates", "certificates"), ("Testimonials", "testimonials"), ("Posts", "posts"),
            ("Contact", "contact"),
        ]
        for i, (name, typ) in enumerate(sections):
            Section.objects.get_or_create(name=name, defaults={"section_type": typ, "order": i})
        social_defaults = [
            ("GitHub", "https://github.com/", "github"),
            ("LinkedIn", "https://www.linkedin.com/", "linkedin"),
            ("Telegram", "https://t.me/", "telegram"),
            ("Instagram", "https://www.instagram.com/", "instagram"),
            ("YouTube", "https://www.youtube.com/", "youtube"),
            ("Facebook", "https://www.facebook.com/", "facebook"),
        ]
        for order, (name, url, icon) in enumerate(social_defaults):
            SocialLink.objects.get_or_create(name=name, defaults={"url": url, "icon": icon, "order": order, "enabled": False})
        self.stdout.write(self.style.SUCCESS("Seed data is ready. Existing records were preserved."))
