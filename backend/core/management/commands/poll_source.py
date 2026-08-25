from django.core.management.base import BaseCommand, CommandError

from core.ingest import ingest_source
from core.models import Source


class Command(BaseCommand):
    help = 'Fetch one source now, by uid. Ignores next_fetch_at — this is the manual override.'

    def add_arguments(self, parser):
        parser.add_argument('source_uid')

    def handle(self, *args, **options):
        try:
            source = Source.objects.get(uid=options['source_uid'])
        except Source.DoesNotExist:
            raise CommandError(f'No source with uid {options["source_uid"]}') from None

        result = ingest_source(source)
        self.stdout.write(f'{source.feed_url} — {result}')
