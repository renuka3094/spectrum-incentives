import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Creates one superuser from DJANGO_SUPERUSER_* environment variables,
    but only if a user with that username doesn't already exist.

    Exists specifically so a deploy host without interactive shell access
    (e.g. Render's free tier, which puts the Shell tab behind a paid plan)
    can still get an admin login — this command is meant to be chained
    onto the end of the Build Command, so it runs automatically on every
    deploy. Safe to run repeatedly: get_or_create-style idempotency means a
    second/third/nth deploy just finds the existing user and does nothing,
    rather than erroring like `createsuperuser --noinput` does on a
    username collision.
    """

    help = (
        "Create a superuser from DJANGO_SUPERUSER_USERNAME / "
        "DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD env vars, "
        "unless one with that username already exists."
    )

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not username or not password:
            self.stdout.write(
                "DJANGO_SUPERUSER_USERNAME/DJANGO_SUPERUSER_PASSWORD not "
                "set — skipping (no admin login created)."
            )
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' already exists — skipping.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
