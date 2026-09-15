from itertools import count

import dramatiq
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client
from django.utils import timezone
from dramatiq.brokers.stub import StubBroker
from dramatiq.worker import Worker

from core.auth import issue_token
from core.models import Feed, Folder, FolderMember, Post, Source

# The whole suite runs against Dramatiq's in-memory broker, and the order of the next three
# statements is load-bearing — hence the isort fence, which stops a reformat from shuffling
# them. Importing core.tasks pulls in feedme/broker.py, which installs the *Redis* broker as
# an import-time side effect, and an actor binds whichever broker is current when its
# decorator runs. So the swap has to land between those two imports: a fixture would be too
# late, the actors would hold a broker wired to the queue the dev worker is consuming, and
# one stray .send() would hand it ids from the throwaway test database.
# isort: off
from feedme.broker import broker as _redis_broker  # noqa: E402

# Same middleware stack, different transport — copied rather than re-listed so the two can't
# drift, and not cosmetic either way: without PeriodiqMiddleware the sweep's `periodic=`
# option is rejected at import, and without the connections middleware a worker thread gets
# a database connection nobody ever closes.
_broker = StubBroker(middleware=list(_redis_broker.middleware))
_broker.emit_after('process_boot')
dramatiq.set_broker(_broker)

from core import tasks  # noqa: E402, F401 — its actors must bind the stub above

# isort: on


@pytest.fixture(autouse=True)
def local_cache(settings):
    """Every test gets an in-process cache in place of settings.py's Redis one.

    Same reason as the stub broker: the dev Redis is live, shared with the worker, and a
    cached YouTube search leaking from one test into the next — or into the running app —
    is exactly the kind of bug that passes green. Django resets the cache handler when
    CACHES changes, so `from django.core.cache import cache` sees the swap. Cleared as
    well, since locmem is one dict for the whole process — safe here, never against Redis.
    """
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
    cache.clear()


@pytest.fixture
def stub_broker():
    """The broker every actor is bound to, flushed so queues don't leak between tests."""
    _broker.flush_all()
    return _broker


@pytest.fixture
def stub_worker(stub_broker):
    """A real worker over the stub broker, for the tests that want a message *executed*."""
    worker = Worker(stub_broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()


@pytest.fixture
def user(db):
    """A plain app user. No usable password — sign-in is Google-only (backend.md § Auth)."""
    return get_user_model().objects.create_user(email='reader@example.com')


@pytest.fixture
def other_user(db):
    """A second account. Every user-scoped endpoint owes a test that this one stays invisible."""
    return get_user_model().objects.create_user(email='someone.else@example.com')


@pytest.fixture
def auth_token(user):
    """The plaintext token for `user` — take this when the test needs the raw string."""
    return issue_token(user, device_label='pytest')


@pytest.fixture
def authed_client(auth_token):
    """A test client sending Authorization: Bearer on every request."""
    return Client(headers={'authorization': f'Bearer {auth_token}'})


# The factories below take the owning user as an argument rather than closing over the
# `user` fixture, so an isolation test can build the same shape for two accounts.


@pytest.fixture
def make_source(db):
    """Sources are global and unique by feed_url, so every call gets its own URL."""
    counter = count(1)

    def _make(**fields):
        n = next(counter)
        fields.setdefault('type', Source.Type.WEBSITE)
        fields.setdefault('feed_url', f'https://example.com/{n}/rss')
        fields.setdefault('title', f'Source {n}')
        return Source.objects.create(**fields)

    return _make


@pytest.fixture
def make_feed(make_source):
    def _make(user, name='A feed', source=None, order=0):
        return Feed.objects.create(
            user=user, source=source or make_source(), name=name, order=order
        )

    return _make


@pytest.fixture
def make_folder(db):
    def _make(user, name='A folder', feeds=(), muted=(), order=0):
        folder = Folder.objects.create(user=user, name=name, order=order)
        for position, feed in enumerate(feeds):
            FolderMember.objects.create(
                folder=folder, feed=feed, order=position, muted=feed in muted
            )
        return folder

    return _make


@pytest.fixture
def make_post(make_source):
    counter = count(1)

    def _make(source=None, **fields):
        n = next(counter)
        fields.setdefault('guid', f'urn:post:{n}')
        fields.setdefault('title', f'Post {n}')
        fields.setdefault('post_url', f'https://example.com/post/{n}')
        fields.setdefault('published_at', timezone.now())
        return Post.objects.create(source=source or make_source(), **fields)

    return _make
