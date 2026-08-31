from ninja import NinjaAPI

from core.api.account import router as account_router
from core.api.errors import register_error_handlers
from core.api.home import router as home_router
from core.api.posts import router as posts_router
from core.api.settings import router as settings_router
from core.auth import BearerAuth

# Global guard: the app is login-only, there is no anonymous surface (backend.md § API).
# Opt an individual operation out with auth=None.
api = NinjaAPI(title='FeedMe API', version='1', auth=BearerAuth())

register_error_handlers(api)


@api.get('/health', auth=None)
def health(request):
    """Unguarded on purpose — the compose healthcheck has no token to present."""
    return {'status': 'ok'}


api.add_router('', account_router)
api.add_router('', home_router)
api.add_router('', posts_router)
api.add_router('', settings_router)
