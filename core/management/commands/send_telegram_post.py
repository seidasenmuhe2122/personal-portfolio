from django.core.management.base import BaseCommand
from core.models import Post
from core.integrations import send_telegram_message
from django.conf import settings


class Command(BaseCommand):
    help = "Send a published post to the configured Telegram channel."

    def add_arguments(self, parser):
        parser.add_argument("slug")

    def handle(self, *args, **opts):
        post = Post.objects.get(slug=opts["slug"])
        public_url = f"{settings.SITE_URL}/blog/{post.slug}/"
        text = f"{post.title}\n\n{post.body[:3200]}\n\n{public_url}".strip()
        # Telegram needs a public URL for sendPhoto; do not send local media paths.
        photo_url = f"{settings.SITE_URL}{post.image.url}" if post.image else None
        result = send_telegram_message(text, photo_url=photo_url)
        if result.get("ok"):
            self.stdout.write(self.style.SUCCESS("Telegram post sent."))
        else:
            self.stderr.write(self.style.ERROR(str(result)))
