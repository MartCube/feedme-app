"""The generated schema is a contract, not a by-product.

T6 generates the frontend's TypeScript from `/api/v1/openapi.json`, so the two things a new
endpoint can silently get wrong — landing in no group, or carrying ninja's auto-generated
operation id — are pinned here rather than noticed in a diff of generated code.
"""

import pytest

from feedme.api import TAGS

DECLARED_TAGS = [tag['name'] for tag in TAGS]


@pytest.fixture
def schema(client):
    return client.get('/api/v1/openapi.json').json()


@pytest.fixture
def operations(schema):
    return [
        (method.upper(), path, operation)
        for path, methods in schema['paths'].items()
        for method, operation in methods.items()
    ]


def test_the_docs_show_the_groups_in_the_declared_order(schema):
    assert [tag['name'] for tag in schema['tags']] == DECLARED_TAGS
    assert all(tag.get('description') for tag in schema['tags'])


def test_every_operation_lands_in_exactly_one_declared_group(operations):
    for method, path, operation in operations:
        assert operation.get('tags') == [operation['tags'][0]], f'{method} {path} has no one tag'
        assert operation['tags'][0] in DECLARED_TAGS, f'{method} {path} is in an unknown group'


def test_operation_ids_are_hand_written_and_unique(operations):
    """ninja derives an id from the module path when you don't pass one, which would put
    `core_api_posts_feed_posts` in the generated client. Every route names its own."""
    ids = [operation['operationId'] for _, _, operation in operations]

    assert len(ids) == len(set(ids))
    for operation_id in ids:
        assert not operation_id.startswith(('core_api_', 'feedme_api_')), operation_id
