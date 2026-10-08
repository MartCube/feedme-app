"""Account-level appearance preferences.

These live on the account rather than in a browser cookie so they follow the user across
devices (backend.md § Endpoint catalog). `sidebarSettingsOpen` deliberately stays on the
client — it's a desktop panel affordance, not a preference worth syncing.

Values are typed as Literals rather than plain strings: ninja then rejects an unknown one
with a 422 for free, and the OpenAPI schema carries the allowed set, so the TypeScript T6
generates from it gets real union types instead of `string`.
"""

from typing import Literal

from ninja import Router, Schema

from ..models import UserSettings
from .errors import ErrorSchema

# tagged `user` alongside account.py — see that module's docstring
router = Router(tags=['user'])


class SettingsSchema(Schema):
    theme: Literal['ink', 'claude']
    feed_list_style: Literal['list', 'cards']
    # 'auto' is the native baseline the app writes no scrollbar rules for; the Appearance
    # panel labels it "System"
    scrollbar_style: Literal['thin', 'comfortable', 'auto']
    # which version of a post card to render: a square image beside the text, or date + title alone
    # (docs/images.md § Rendering)
    post_card_style: Literal['image', 'compact']
    # desktop only: which reading pane is the wider one — the posts list, the post, or
    # neither (a 50/50 split)
    pane_split: Literal['posts', 'equal', 'post']


@router.get(
    '/settings', response={200: SettingsSchema, 401: ErrorSchema}, operation_id='get_settings'
)
def get_settings(request):
    # Nothing creates a UserSettings row today, so most first reads find none. Answer from
    # an unsaved instance holding the model defaults rather than get_or_create: a read
    # shouldn't cause a write (the rule T2 set with expired tokens). The row appears on the
    # first PUT, which is the first time there's anything worth storing.
    user_settings = UserSettings.objects.filter(user=request.auth).first()
    return user_settings or UserSettings(user=request.auth)


@router.put(
    '/settings',
    response={200: SettingsSchema, 401: ErrorSchema, 422: ErrorSchema},
    operation_id='set_settings',
)
def put_settings(request, payload: SettingsSchema):
    # A full replace, true to the verb: every field is required, so there's no ambiguity
    # about what an omitted one means.
    user_settings, _ = UserSettings.objects.update_or_create(
        user=request.auth, defaults=payload.model_dump()
    )
    return user_settings
