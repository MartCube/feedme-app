"""The background jobs. Names come from docs/backend.md § Fetching pipeline's job table.

Nothing here re-implements polling — T3 wrote `ingest_source` as a plain function precisely
so this task could wrap it without a rewrite, and `manage.py poll_due` / `poll_source` still
drive the same function by hand when you want to poll without a worker running.

Import order below is load-bearing: `feedme.broker` calls `django.setup()` and installs the
Redis broker, so it has to be imported before `.ingest` (which reaches models) and before the
`@dramatiq.actor` decorators, which bind whichever broker is current when they run. ruff's
import grouping keeps it there for free — first-party `feedme` sorts above the local `.`
imports — so don't hand-reorder this block.
"""

import logging

import dramatiq
from django.utils import timezone
from periodiq import cron

from feedme import broker  # noqa: F401 — imported for its import-time side effects

from . import retention
from .ingest import POLL_INTERVAL, due_sources, ingest_source
from .models import Source

logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=3, min_backoff=15_000, max_backoff=300_000, time_limit=120_000)
def poll_source(source_uid):
    """Fetch one source and upsert its posts.

    The retry settings cover what can *throw* — a database blip, a bug, a killed worker.
    A feed being down is not one of those: `ingest_source` never raises, and the source's
    own `error_count` / `next_fetch_at` backoff is the retry schedule for that. Two error
    models that deliberately don't overlap.

    The time limit is two minutes: comfortably above the worst case ingest's own (5, 15)
    HTTP timeouts allow, and far below Dramatiq's ten-minute default.
    """
    source = Source.objects.filter(uid=source_uid).first()
    if source is None:
        # A real race, not a theoretical one: POST /feeds deletes a source whose first
        # fetch failed. Returning quietly matters — raising would burn a retry on a row
        # that is never coming back.
        logger.info('poll_source: %s no longer exists', source_uid)
        return
    if not source.active:
        # deactivated by the last subscriber leaving, or by five consecutive failures
        logger.info('poll_source: %s is inactive, skipping', source.feed_url)
        return

    logger.info('poll_source: %s — %s', source.feed_url, ingest_source(source))


@dramatiq.actor(max_retries=0, periodic=cron('*/5 * * * *'))
def poll_due_sources():
    """The scheduler's sweep: enqueue every source whose next_fetch_at has passed.

    Every five minutes, against a ~30-minute per-source cadence (POLL_INTERVAL, jittered
    ±10% in core/ingest.py) — so at most five minutes of lateness, and twelve times fewer
    wake-ups than a per-minute sweep.

    No retries: a failed sweep is covered by the next one, and retrying it would enqueue
    the same sources twice.
    """
    now = timezone.now()
    uids = list(due_sources(now).values_list('uid', flat=True))
    if not uids:
        logger.debug('poll_due_sources: nothing due')
        return

    # Claim the batch before sending. `ingest_source` only pushes next_fetch_at out when it
    # *finishes*, so without this the next sweep re-enqueues everything still queued or in
    # flight. The claimed value is where a successful poll would have landed anyway, and the
    # poll overwrites it with the real schedule (or the failure backoff). If this process
    # dies between the claim and the send, that source waits one interval — the cheap failure.
    Source.objects.filter(uid__in=uids).update(next_fetch_at=now + POLL_INTERVAL)
    for uid in uids:
        poll_source.send(uid)
    logger.info('poll_due_sources: enqueued %d source(s)', len(uids))


# The two retention sweeps, both daily and both wrapping a plain function in core/retention.py
# the same way poll_source wraps ingest. max_retries=3 rather than poll_due_sources' 0: that
# sweep can afford to wait five minutes for the next one, these would wait a full day, and the
# work is idempotent and batched so a retry simply resumes where the last attempt stopped.


@dramatiq.actor(max_retries=3, periodic=cron('30 3 * * *'), time_limit=900_000)
def prune_posts():
    """Delete unsaved posts past the retention window or beyond their source's cap.

    The time limit is fifteen minutes, above Dramatiq's ten-minute default, because the
    first run against a table nothing has ever pruned is the large one — every run after
    it only has a day's worth to catch.
    """
    logger.info('prune_posts: deleted %s', retention.prune_posts())


@dramatiq.actor(max_retries=3, periodic=cron('45 3 * * *'))
def prune_expired_tokens():
    """Delete token rows already past their sliding window. See core/auth.py."""
    logger.info('prune_expired_tokens: deleted %d row(s)', retention.prune_expired_tokens())
