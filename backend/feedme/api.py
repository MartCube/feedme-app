from ninja import NinjaAPI

from core.api.account import router as account_router
from core.api.discover import router as discover_router
from core.api.errors import register_error_handlers
from core.api.feeds import router as feeds_router
from core.api.folders import router as folders_router
from core.api.home import router as home_router
from core.api.posts import router as posts_router
from core.api.search import router as search_router
from core.api.settings import router as settings_router
from core.auth import BearerAuth

# Each router declares its own tag; this list only sets the order the docs UI shows the
# groups in (it sorts alphabetically otherwise) and gives each one a line of explanation.
# A tag named here that no operation uses is simply not rendered.
TAGS = [
    {
        'name': 'home',
        'description': 'The home screen in one round-trip, and the write that reorders it.',
    },
    {
        'name': 'feeds',
        'description': (
            'Reading. The post list takes a polymorphic uid — all, saved, a saved group '
            '(saved_*), a folder (folder_*) or a single feed (feed_*) — plus post detail '
            'and the save toggle.'
        ),
    },
    {
        'name': 'user',
        'description': 'The signed-in account: identity, sessions, and appearance settings.',
    },
    {'name': 'default', 'description': 'Unauthenticated service endpoints.'},
]

# Global guard: the app is login-only, there is no anonymous surface (backend.md § API).
# Opt an individual operation out with auth=None.
api = NinjaAPI(title='FeedMe API', version='1', auth=BearerAuth(), openapi_extra={'tags': TAGS})

register_error_handlers(api)


@api.get('/health', auth=None, tags=['default'], operation_id='health')
def health(request):
    """Unguarded on purpose — the compose healthcheck has no token to present."""
    return {'status': 'ok'}


api.add_router('', account_router)
api.add_router('', home_router)
api.add_router('', folders_router)
api.add_router('', feeds_router)
api.add_router('', discover_router)
api.add_router('', posts_router)
api.add_router('', search_router)
api.add_router('', settings_router)
