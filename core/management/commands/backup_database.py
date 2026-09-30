from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a timestamped JSON backup of application data."

    def handle(self, *args, **kwargs):
        out = Path(settings.BASE_DIR) / "backups"
        out.mkdir(exist_ok=True)
        path = out / f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with path.open("w", encoding="utf-8") as f:
            management.call_command("dumpdata", "core", stdout=f, indent=2)
        self.stdout.write(self.style.SUCCESS(f"Backup created: {path}"))
