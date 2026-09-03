"""The queue layer: the sweep that enqueues, and the actor that polls.

What polling itself does is test_ingest.py's job — these tests cover what the queue adds:
which sources get enqueued, that they get enqueued exactly once, and what the actor does
with a uid whose source has moved on since the sweep named it.
"""

from datetime import timedelta

import pytest
import requests
from django.utils import timezone
from dramatiq import Message

from core import tasks
from core.models import Post, Source
from tests import feeds

# T3's network seam and its 200 helper — the actor tests need exactly the same fake.
from tests.test_ingest import ok, serve


@pytest.fixture
def source(db):
    return Source.objects.create(
        type=Source.Type.WEBSITE, feed_url='https://medium.com/feed/tag/vuejs'
    )


def queued_uids(broker):
    """Every uid sitting on the poll queue, in order, without consuming the messages.

    A list rather than a set on purpose: the duplicate is what the claim test is looking for.
    """
    queue = broker.queues[tasks.poll_source.queue_name]
    return [Message.decode(data).args[0] for data in list(queue.queue)]


def test_the_sweep_enqueues_one_message_per_due_source(db, stub_broker):
    never_polled = Source.objects.create(type=Source.Type.WEBSITE, feed_url='https://a.example/rss')
    overdue = Source.objects.create(
        type=Source.Type.WEBSITE,
        feed_url='https://b.example/rss',
        next_fetch_at=timezone.now() - timedelta(minutes=1),
    )

    tasks.poll_due_sources.fn()

    assert sorted(queued_uids(stub_broker)) == sorted([never_polled.uid, overdue.uid])


def test_the_sweep_leaves_a_source_that_is_not_due_alone(db, stub_broker):
    Source.objects.create(
        type=Source.Type.WEBSITE,
        feed_url='https://c.example/rss',
        next_fetch_at=timezone.now() + timedelta(hours=1),
    )

    tasks.poll_due_sources.fn()

    assert queued_uids(stub_broker) == []


def test_the_sweep_leaves_a_deactivated_source_alone(db, stub_broker):
    Source.objects.create(type=Source.Type.WEBSITE, feed_url='https://d.example/rss', active=False)

    tasks.poll_due_sources.fn()

    assert queued_uids(stub_broker) == []


def test_the_sweep_claims_what_it_enqueues_so_the_next_one_does_not_repeat(source, stub_broker):
    """ingest only pushes next_fetch_at out when a poll *finishes*. Until then the claim is
    the only thing keeping a five-minute sweep from enqueueing the same source again."""
    tasks.poll_due_sources.fn()

    tasks.poll_due_sources.fn()  # nothing has run the poll yet

    assert queued_uids(stub_broker) == [source.uid]
    source.refresh_from_db()
    assert source.next_fetch_at > timezone.now()


def test_the_actor_polls_the_source_it_names(source, monkeypatch):
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    tasks.poll_source.fn(source.uid)

    assert Post.objects.filter(source=source).count() == 2


def test_the_actor_shrugs_off_a_uid_whose_source_is_gone(db):
    """POST /feeds deletes a source whose first fetch failed, so this really happens — and
    raising would burn a retry on a row that is never coming back."""
    tasks.poll_source.fn('source_deletedmidflight')

    assert not Post.objects.exists()


def test_the_actor_skips_a_deactivated_source(source, monkeypatch):
    source.active = False
    source.save(update_fields=['active'])
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    tasks.poll_source.fn(source.uid)

    assert not Post.objects.exists()


def test_a_dead_feed_never_raises_out_of_the_actor(source, monkeypatch):
    """Dramatiq's retries are for what throws. A feed being down is not that — it is the
    source's own error_count and backoff, and the two must not double up."""
    serve(monkeypatch, requests.ConnectionError('name or service not known'))

    tasks.poll_source.fn(source.uid)

    source.refresh_from_db()
    assert source.error_count == 1


@pytest.mark.django_db(transaction=True)
def test_a_sent_message_reaches_a_worker_and_polls(stub_broker, stub_worker, monkeypatch):
    """The one test that goes the whole way: encode, enqueue, consume, decode, run — which
    also exercises the middleware that hands the worker thread a usable connection."""
    source = Source.objects.create(
        type=Source.Type.WEBSITE, feed_url='https://medium.com/feed/tag/vuejs'
    )
    serve(monkeypatch, ok(feeds.RSS_BLOG))

    tasks.poll_source.send(source.uid)
    stub_broker.join(tasks.poll_source.queue_name)
    stub_worker.join()

    assert Post.objects.filter(source=source).count() == 2
