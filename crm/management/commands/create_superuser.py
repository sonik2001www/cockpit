from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ["DJANGO_SUPERUSER_USERNAME"]
        password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
        email = os.environ["DJANGO_SUPERUSER_EMAIL"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        user.set_password(password)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.save()
