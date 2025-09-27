from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
import os


class Command(BaseCommand):

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ["DJANGO_SUPERUSER_USERNAME"]
        password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
        email = os.environ["DJANGO_SUPERUSER_EMAIL"]
        fixed_token = os.environ.get("TOKEN")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        user.set_password(password)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.save()

        Token.objects.filter(user=user).delete()

        if fixed_token:
            token = Token.objects.create(user=user, key=fixed_token)
        else:
            token = Token.objects.create(user=user)
