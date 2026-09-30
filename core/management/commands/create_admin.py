from getpass import getpass
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a superuser interactively if none exists."

    def add_arguments(self, parser):
        parser.add_argument("--username")
        parser.add_argument("--email")

    def handle(self, *args, **opts):
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING("A superuser already exists; nothing was changed."))
            return
        username = opts.get("username") or input("Username: ").strip()
        email = opts.get("email") or input("Email: ").strip()
        password = getpass("Password: ")
        confirm = getpass("Password again: ")
        if not username or not email or not password:
            raise CommandError("Username, email and password are required.")
        if password != confirm:
            raise CommandError("Passwords do not match.")
        user = User.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS(f"Superuser {user.username} created."))
