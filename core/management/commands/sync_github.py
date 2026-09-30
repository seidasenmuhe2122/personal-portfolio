from django.core.management.base import BaseCommand
from core.models import Project
from core.integrations import github_repo


class Command(BaseCommand):
    help = "Sync GitHub metadata into projects that have github_repo configured."

    def handle(self, *args, **kwargs):
        count = 0
        for project in Project.objects.exclude(github_repo=""):
            try:
                data = github_repo(project.github_repo)
                if data.get("html_url"):
                    project.source_url = data["html_url"]
                    project.summary = data.get("description") or project.summary
                    project.save(update_fields=["source_url", "summary", "updated_at"])
                    count += 1
            except Exception:
                continue
        self.stdout.write(self.style.SUCCESS(f"Synced {count} projects."))
