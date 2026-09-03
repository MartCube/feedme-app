"""The Dramatiq broker, and the two things a Django worker needs that Dramatiq doesn't do.

Imported first by core/tasks.py, which makes `core.tasks` the entry module for both CLIs:

    dramatiq core.tasks --processes 2 --threads 4    # the worker, runs the actors
    periodiq -v core.tasks                           # the scheduler, only enqueues

Nothing here runs during a normal request — the api process picks the same broker up if it
ever sends a message, but today only the worker consumes and only the scheduler enqueues.
"""

import os

import django

# Load-bearing for the CLIs and no-ops under manage.py: dramatiq's CLI imports its module
# argument with a plain importlib call inside each forked worker process, and never
# configures Django. Without this, importing core.models below raises ImproperlyConfigured.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedme.settings')
django.setup()

import dramatiq  # noqa: E402 — must follow django.setup()
from django.conf import settings  # noqa: E402
from django.db import close_old_connections  # noqa: E402
from dramatiq.brokers.redis import RedisBroker  # noqa: E402
from periodiq import PeriodiqMiddleware  # noqa: E402


class DjangoConnections(dramatiq.Middleware):
    """Close Django's stale database connections around every message.

    The worker is threaded and Django's connections are thread-local, but nothing in a
    worker fires the request-started / request-finished signals that normally close them.
    Without this they accumulate one per thread and are never reaped — a connection that
    Postgres has already dropped stays in the pool, and the count only grows.
    """

    def before_process_message(self, broker, message):
        close_old_connections()

    def after_process_message(self, broker, message, *, result=None, exception=None):
        close_old_connections()


# RedisBroker already carries Dramatiq's defaults (AgeLimit, TimeLimit, Callbacks, Retries).
broker = RedisBroker(url=settings.REDIS_URL)
broker.add_middleware(PeriodiqMiddleware())
broker.add_middleware(DjangoConnections())
dramatiq.set_broker(broker)
