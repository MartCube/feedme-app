"""What retention deletes, and — the load-bearing half — what it never does.

Two rules, both about keeping the posts table and its two GIN indexes bounded rather than
about correctness: a reader is about recent content (docs/backend.md § Data model). A post
dies if *either* catches it. The age window handles a slow source accumulating over years;
the per-source cap handles a firehose that publishes a year's worth in a week.

**A saved post is never deleted** — at any age, by either rule. That exemption is why both
passes run through `_unsaved()` rather than deleting straight off a date, and it is scoped
to "saved by anyone": posts are global rows, so an owner-scoped rule would delete a post
out from under another account's saved pile.

Plain synchronous functions, for the same reason `core/ingest.py` holds one: `core/tasks.py`
wraps these in daily actors, and `manage.py prune_posts` calls them with no broker running.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from .auth import TOKEN_TTL
from .models import AuthToken, Post, SavedPost, Source

RETENTION = timedelta(days=90)
PER_SOURCE_CAP = 500
# pks per DELETE. An unbatched .delete() collects every pk into memory and holds one
# transaction for the whole run; the first prune against a mature table is the big one.
BATCH_SIZE = 1000


@dataclass(frozen=True)
class PruneResult:
    """Shaped after ingest.IngestResult: the actor and the command both log one line."""

    by_age: int = 0
    by_cap: int = 0

    @property
    def total(self):
        return self.by_age + self.by_cap

    def __str__(self):
        return f'{self.total} post(s) — {self.by_age} past the window, {self.by_cap} past the cap'


def prune_posts(*, days=None, cap=None, dry_run=False):
    """Delete unsaved posts past the age window or beyond their source's cap.

    `days` and `cap` override the constants for one run — that is what makes them tunable
    without a deploy (`manage.py prune_posts --days N --cap N`).
    """
    cutoff = age_cutoff(days)
    cap = PER_SOURCE_CAP if cap is None else cap

    if not dry_run:
        return _prune(cutoff, cap)

    # A dry run is the real thing, rolled back. The cap pass runs on what the age pass
    # leaves behind, so simulating it would mean re-deriving that in a second code path
    # that can disagree with the first — and a preview that lies is worse than no preview.
    # The cost is one transaction held for the length of the run, which a deliberate
    # manual command can afford.
    with transaction.atomic():
        result = _prune(cutoff, cap)
        transaction.set_rollback(True)
    return result


def prune_expired_tokens():
    """Delete the token rows the guard already refuses. Returns how many went.

    TOKEN_TTL is imported rather than restated, so this can never drift from the expiry
    test in core/auth.py's BearerAuth. Every row it removes already answers 401, so it can
    end no live session — this is the sweep T2's "the rows are inert" decision pointed at.
    """
    deleted, _ = AuthToken.objects.filter(last_used_at__lt=timezone.now() - TOKEN_TTL).delete()
    return deleted


def age_cutoff(days=None):
    """The published_at below which a post is past the window.

    The only place the line is computed. core/ingest.py reads it too, and that is not a
    convenience: a poll that recreated the posts this job had just deleted would leave the
    two fighting over the same rows every night.
    """
    return timezone.now() - (RETENTION if days is None else timedelta(days=days))


def _prune(cutoff, cap):
    by_age = _delete_in_batches(_unsaved().filter(published_at__lt=cutoff))
    by_cap = 0
    # One source at a time: the cap is per source, and a window function over the whole
    # table would trade the (source, -published_at) index for a sort.
    for source_pk in Source.objects.values_list('pk', flat=True):
        by_cap += _delete_in_batches(_beyond_cap(source_pk, cap))
    return PruneResult(by_age=by_age, by_cap=by_cap)


def _unsaved():
    """Posts nobody has saved. A correlated EXISTS, not a join on Post.saves.

    `filter(saves__isnull=True)` is the join spelling, and T5's decision log records why
    the multi-valued relation is worth avoiding: Django's join reuse is not the one you
    would guess. A subquery cannot multiply the rows it filters.
    """
    return Post.objects.filter(~Exists(SavedPost.objects.filter(post=OuterRef('pk'))))


def _beyond_cap(source_pk, cap):
    """One source's unsaved posts outside its newest `cap`, by published date.

    The keep set is an `IN` against a sliced subquery, so it stays in Postgres instead of
    coming back as a list of pks to send straight out again. (LIMIT inside IN is rejected
    by MySQL; this project is Postgres-only, which migration 0004's extension already
    assumes.) Excluding the keep set is exact where comparing against the boundary row's
    timestamp is not: `-pk` breaks ties, so a source that stamps a whole batch with the
    same second keeps exactly `cap` posts rather than the whole tied group.

    Ranking counts saved posts too — a saved post holds its slot and survives regardless,
    so the cap is a bound on what polling accumulates, not on what a reader kept.
    """
    newest = (
        Post.objects.filter(source=source_pk).order_by('-published_at', '-pk').values('pk')[:cap]
    )
    return _unsaved().filter(source=source_pk).exclude(pk__in=newest)


def _delete_in_batches(posts):
    """Delete a queryset a batch of pks at a time, returning how many posts went.

    The count comes from the per-model dict rather than the total, which would also carry
    any cascaded rows. Nothing cascades today — only unsaved posts get here, so no
    SavedPost row can hang off one — and reading the label keeps that true by accident
    rather than by luck.
    """
    deleted = 0
    while True:
        batch = list(posts.values_list('pk', flat=True)[:BATCH_SIZE])
        if not batch:
            return deleted
        deleted += Post.objects.filter(pk__in=batch).delete()[1].get(Post._meta.label, 0)
