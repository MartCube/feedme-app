from ninja import NinjaAPI

api = NinjaAPI(title='FeedMe API', version='1')


@api.get('/health')
def health(request):
    return {'status': 'ok'}
