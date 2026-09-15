"""Retention: what gets deleted, and — the part with no exceptions — what survives.

Most of these tests assert that something is *still there* afterwards. That is the shape of
the feature: deleting old rows is easy, and the only way to get it wrong that matters is
taking a post somebody saved.
"""

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from core import retention, tasks
from core.auth import TOKEN_TTL, issue_token
from core.ingest import ingest_source
from core.models import AuthToken, Post, SavedPost, Source
from tests import feeds

# T3's network seam and its 200 helper, the same pair test_tasks.py borrows.
from tests.test_ingest import ok, serve


def days_ago(n):
    return timezone.now() - timedelta(days=n)


def save(user, post, group=SavedPost.Group.BOOKMARKS):
    return SavedPost.objects.create(user=user, post=post, group=group)


@pytest.fixture
def year_window(monkeypatch):
    """Widen the window to a year — for both jobs at once, which is the point.

    They read the line from one place (`retention.age_cutoff`), so one patch moves both.
    A year also keeps these tests off the calendar: the archive fixture's 2026 entry is
    inside it and its 2019 entry is outside it whatever today happens to be.
    """
    monkeypatch.setattr(retention, 'RETENTION', timedelta(days=365))


ARCHIVED_GUID = 'https://nuxt.com/blog/introducing-smart-prefetching'


def test_an_unsaved_post_past_the_window_is_deleted(make_source, make_post):
    source = make_source()
    old = make_post(source=source, published_at=days_ago(120))
    recent = make_post(source=source, published_at=days_ago(10))

    result = retention.prune_posts()

    assert result.by_age == 1
    assert list(Post.objects.all()) == [recent]
    assert not Post.objects.filter(pk=old.pk).exists()


def test_a_saved_post_survives_the_window_however_old_it_is(user, make_post):
    ancient = make_post(published_at=days_ago(4000))
    save(user, ancient)

    result = retention.prune_posts()

    assert result.by_age == 0
    assert Post.objects.filter(pk=ancient.pk).exists()


def test_a_post_saved_by_someone_else_survives(other_user, make_post):
    """Posts are global rows, so the exemption is "saved by anyone", not "saved by the
    reader who follows it" — an owner-scoped rule would delete a post out from under
    another account's pile."""
    old = make_post(published_at=days_ago(200))
    save(other_user, old)

    retention.prune_posts()

    assert Post.objects.filter(pk=old.pk).exists()


def test_every_saved_group_is_exempt(user, make_source, make_post):
    source = make_source()
    for group in SavedPost.Group:
        save(user, make_post(source=source, published_at=days_ago(500)), group=group)

    retention.prune_posts()

    assert Post.objects.count() == 3


def test_a_source_outlives_the_posts_pruned_from_it(make_source, make_post):
    """T7 decided a source outlives its last subscriber; pruning its posts is not a way in
    through the back door."""
    source = make_source()
    make_post(source=source, published_at=days_ago(200))

    retention.prune_posts()

    assert not Post.objects.exists()
    assert Source.objects.filter(pk=source.pk).exists()


def test_the_cap_keeps_the_newest_posts_of_a_source(make_source, make_post):
    source = make_source()
    posts = [make_post(source=source, published_at=days_ago(n)) for n in range(1, 6)]

    result = retention.prune_posts(cap=2)

    assert (result.by_age, result.by_cap) == (0, 3)
    assert set(Post.objects.values_list('pk', flat=True)) == {posts[0].pk, posts[1].pk}


def test_the_cap_is_per_source_not_global(make_source, make_post):
    for _ in range(2):
        source = make_source()
        for n in range(1, 4):
            make_post(source=source, published_at=days_ago(n))

    result = retention.prune_posts(cap=3)

    assert result.by_cap == 0
    assert Post.objects.count() == 6


def test_a_saved_post_beyond_the_cap_survives(user, make_source, make_post):
    source = make_source()
    posts = [make_post(source=source, published_at=days_ago(n)) for n in range(1, 6)]
    save(user, posts[4])  # the oldest, well outside a cap of two

    result = retention.prune_posts(cap=2)

    assert result.by_cap == 2
    assert Post.objects.filter(pk=posts[4].pk).exists()


def test_posts_tied_on_published_at_still_leave_exactly_the_cap_standing(make_source, make_post):
    """Comparing against the boundary row's timestamp would keep the whole tied group.
    Excluding the newest `cap` pks, tie-broken on pk, keeps exactly the cap."""
    source = make_source()
    stamp = days_ago(1)
    for _ in range(5):
        make_post(source=source, published_at=stamp)

    result = retention.prune_posts(cap=2)

    assert result.by_cap == 3
    assert Post.objects.count() == 2


def test_a_candidate_set_larger_than_a_batch_is_fully_deleted(monkeypatch, make_source, make_post):
    monkeypatch.setattr(retention, 'BATCH_SIZE', 2)
    source = make_source()
    for n in range(1, 6):
        make_post(source=source, published_at=days_ago(100 + n))

    result = retention.prune_posts()

    assert result.by_age == 5
    assert not Post.objects.exists()


def test_a_dry_run_reports_the_counts_and_deletes_nothing(make_post):
    make_post(published_at=days_ago(200))

    result = retention.prune_posts(dry_run=True)

    assert result.by_age == 1
    assert Post.objects.count() == 1


def test_a_dry_run_sees_what_the_age_pass_leaves_for_the_cap_pass(make_source, make_post):
    """The cap ranks what survives the age pass, not what started there. Running for real
    and rolling back gets that right by construction; a simulated preview would have to
    re-derive it and could disagree — here it would claim more deletions than there are
    posts."""
    source = make_source()
    for n in range(1, 4):
        make_post(source=source, published_at=days_ago(100 + n))
    for n in range(1, 4):
        make_post(source=source, published_at=days_ago(n))

    dry = retention.prune_posts(cap=2, dry_run=True)
    real = retention.prune_posts(cap=2)

    assert (dry.by_age, dry.by_cap) == (real.by_age, real.by_cap) == (3, 1)
    assert Post.objects.count() == 2


def test_the_posts_actor_prunes(make_post):
    make_post(published_at=days_ago(200))

    tasks.prune_posts.fn()

    assert not Post.objects.exists()


def test_an_expired_token_row_is_deleted(user):
    issue_token(user, device_label='a phone last seen in spring')
    AuthToken.objects.update(last_used_at=timezone.now() - TOKEN_TTL - timedelta(days=1))

    assert retention.prune_expired_tokens() == 1
    assert not AuthToken.objects.exists()


def test_a_token_inside_its_window_is_kept(user):
    """The same test BearerAuth applies, so this can only ever remove rows that already
    answer 401 — pruning can't sign anybody out."""
    issue_token(user, device_label='daily driver')

    assert retention.prune_expired_tokens() == 0
    assert AuthToken.objects.count() == 1


def test_the_token_actor_prunes(user):
    issue_token(user)
    AuthToken.objects.update(last_used_at=timezone.now() - TOKEN_TTL - timedelta(hours=1))

    tasks.prune_expired_tokens.fn()

    assert not AuthToken.objects.exists()


def test_the_command_deletes_and_reports(make_post):
    make_post(published_at=days_ago(200))
    out = StringIO()

    call_command('prune_posts', stdout=out)

    assert not Post.objects.exists()
    assert 'Deleted 1 post(s)' in out.getvalue()


def test_the_command_dry_run_deletes_nothing(make_post):
    make_post(published_at=days_ago(200))
    out = StringIO()

    call_command('prune_posts', '--dry-run', stdout=out)

    assert Post.objects.count() == 1
    assert 'Would delete 1 post(s)' in out.getvalue()


def test_the_command_flags_override_the_constants(make_source, make_post):
    source = make_source()
    for n in (1, 5, 10):
        make_post(source=source, published_at=days_ago(n))

    call_command('prune_posts', '--days', '7', '--cap', '1', stdout=StringIO())

    assert Post.objects.count() == 1


# Polling and pruning have to agree about the window, or they undo each other nightly.


def test_polling_does_not_create_a_post_already_past_the_window(
    year_window, monkeypatch, make_source
):
    source = make_source(feed_url='https://nuxt.com/blog/rss.xml')
    serve(monkeypatch, ok(feeds.RSS_ARCHIVE))

    result = ingest_source(source)

    assert (result.created, result.updated) == (1, 0)
    assert [p.title for p in Post.objects.all()] == ['Announcing Nuxt 4']


def test_polling_still_updates_a_post_that_has_aged_out_of_the_window(
    year_window, monkeypatch, make_source, make_post
):
    """A saved post outlives the window, so it has to keep tracking what its source says."""
    source = make_source(feed_url='https://nuxt.com/blog/rss.xml')
    stale = make_post(
        source=source, title='Stale title', guid=ARCHIVED_GUID, published_at=days_ago(2500)
    )
    serve(monkeypatch, ok(feeds.RSS_ARCHIVE))

    ingest_source(source)

    stale.refresh_from_db()
    assert stale.title == 'Introducing Smart Prefetching'
    assert Post.objects.count() == 2


def test_a_pruned_post_does_not_come_back_on_the_next_poll(
    year_window, monkeypatch, make_source, make_post
):
    """The loop this rule exists to close, and it was found against the real dev database
    rather than here: the prune took 49 posts off an archive feed, and the sweep five
    minutes later put all 49 back with new uids and empty article caches."""
    source = make_source(feed_url='https://nuxt.com/blog/rss.xml')
    make_post(source=source, guid=ARCHIVED_GUID, published_at=days_ago(2500))
    serve(monkeypatch, ok(feeds.RSS_ARCHIVE))

    assert retention.prune_posts().by_age == 1
    ingest_source(source)

    assert [p.title for p in Post.objects.all()] == ['Announcing Nuxt 4']
