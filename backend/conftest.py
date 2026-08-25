from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from core.auth import issue_token
from core.models import Feed, Folder, FolderMember, Post, Source


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
