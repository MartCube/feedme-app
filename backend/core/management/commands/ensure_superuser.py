import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create the admin superuser from DJANGO_SUPERUSER_EMAIL/PASSWORD if it does not exist.'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not email or not password:
            self.stdout.write('DJANGO_SUPERUSER_* not set — skipping superuser creation')
            return
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            return
        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Created superuser {email}'))
