from django.core.management.base import BaseCommand

from core.ingest import due_sources, ingest_source


class Command(BaseCommand):
    help = 'Fetch every active source whose next_fetch_at is due. T9 moves this onto a scheduler.'

    def handle(self, *args, **options):
        sources = list(due_sources())
        if not sources:
            self.stdout.write('Nothing due.')
            return

        created = 0
        deactivated = 0
        for source in sources:
            result = ingest_source(source)
            created += result.created
            deactivated += not source.active
            self.stdout.write(f'{source.feed_url} — {result}')

        summary = f'Polled {len(sources)} source(s), {created} new post(s).'
        if deactivated:
            summary += f' {deactivated} deactivated after repeated failures.'
        self.stdout.write(self.style.SUCCESS(summary))
