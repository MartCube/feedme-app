from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from core.auth import issue_token


class Command(BaseCommand):
    help = 'Print a new bearer token for a user. Dev only — T8 replaces this with Google sign-in.'

    def add_arguments(self, parser):
        parser.add_argument('email')
        parser.add_argument('--device-label', default='dev')

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(email=options['email'])
        except User.DoesNotExist:
            raise CommandError(f'No user with email {options["email"]}') from None

        # bare write, no style.SUCCESS: the output is meant to be piped or pasted,
        # so it must be the token and nothing else
        self.stdout.write(issue_token(user, device_label=options['device_label']))
