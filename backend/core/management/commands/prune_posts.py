from django.core.management.base import BaseCommand

from core import retention


class Command(BaseCommand):
    help = (
        "Delete unsaved posts past the retention window or beyond their source's cap. The "
        'scheduler does this daily — this is the manual override, and it needs no broker '
        'running. Saved posts are never deleted, at any age.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help=f'Age window in days (default {retention.RETENTION.days})',
        )
        parser.add_argument(
            '--cap',
            type=int,
            help=f'Newest posts kept per source (default {retention.PER_SOURCE_CAP})',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run for real inside a transaction and roll it back — report, delete nothing',
        )

    def handle(self, *args, **options):
        result = retention.prune_posts(
            days=options['days'], cap=options['cap'], dry_run=options['dry_run']
        )
        if options['dry_run']:
            self.stdout.write(f'Would delete {result}.')
            return
        self.stdout.write(self.style.SUCCESS(f'Deleted {result}.'))
