from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AuthToken,
    Feed,
    FeedSource,
    Post,
    SavedPost,
    Source,
    User,
    UserSettings,
)

# Everything a user owns — settings, feeds, saved posts, sessions — is edited from
# the user's own page, because that is the question admin gets asked first: what does this
# account actually have? Only the global tables (Source and Post, one copy shared by every
# subscriber) and the accounts themselves are listed on the index.


class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False
    max_num = 1
    # stacked.html titles each form from verbose_name, not the plural, so both are set
    verbose_name = 'Appearance settings'
    verbose_name_plural = 'Appearance settings'
    # The row is created by the first PUT /settings, not at signup (a read never writes —
    # core/api/settings.py), so an account can legitimately have none yet and the form has
    # to offer to add it.


class FeedInline(admin.TabularInline):
    model = Feed
    extra = 0
    fields = ('name', 'order', 'uid')
    readonly_fields = ('uid',)
    show_change_link = True
    verbose_name_plural = 'Feeds (groups of sources)'
    # A feed's sources and their on/off are edited on the feed's own page: Django admin has
    # no nested inlines, so FeedSourceInline cannot ride along inside this one. The change
    # link on each row is the way through.


class SavedPostInline(admin.TabularInline):
    model = SavedPost
    extra = 0
    fields = ('post', 'group', 'saved_at')
    readonly_fields = ('saved_at',)
    autocomplete_fields = ('post',)
    verbose_name_plural = 'Saved posts'


class AuthTokenInline(admin.TabularInline):
    model = AuthToken
    extra = 0
    fields = ('device_label', 'created_at', 'last_used_at')
    readonly_fields = fields
    verbose_name_plural = 'Sessions (bearer tokens)'

    def has_add_permission(self, request, obj=None):
        """Deleting a row is the revoke button; issuing is `manage.py issue_token`, which is
        the only place the plaintext token ever exists — admin only ever sees the hash."""
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'google_sub', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email',)
    # password is a hash — managed by createsuperuser / ensure_superuser, not edited raw
    exclude = ('password',)
    readonly_fields = ('created_at', 'last_login', 'saved_posts_link')
    inlines = (
        UserSettingsInline,
        FeedInline,
        SavedPostInline,
        AuthTokenInline,
    )

    @admin.display(description='All saved posts')
    def saved_posts_link(self, user):
        """The inline above edits the pile; this reaches the filtered changelist, which is
        the readable view once an account has saved more rows than fit on a form."""
        if user.pk is None:
            return '—'
        url = reverse('admin:core_savedpost_changelist')
        count = user.saved_posts.count()
        return format_html('<a href="{}?user__id__exact={}">{} saved</a>', url, user.pk, count)


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_label', 'created_at', 'last_used_at')
    list_filter = ('user',)
    search_fields = ('user__email',)
    readonly_fields = ('token_hash', 'created_at', 'last_used_at')


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'type',
        'active',
        'error_count',
        'last_fetched_at',
        'next_fetch_at',
        'feed_url',
    )
    list_filter = ('type', 'active')
    search_fields = ('title', 'feed_url', 'site_url')
    readonly_fields = ('uid',)
    actions = ('reset_and_reschedule',)

    @admin.action(description='Reset errors and poll on the next run')
    def reset_and_reschedule(self, request, queryset):
        """The way back from an automatic deactivation (core/ingest.py § _record_failure).

        Doesn't poll inline — that would hold the admin request open for a network call
        per source. Clearing next_fetch_at makes them due, then `poll_due` picks them up.
        """
        count = queryset.update(active=True, error_count=0, next_fetch_at=None)
        self.message_user(request, f'{count} source(s) reset — due on the next poll.')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_at')
    list_select_related = ('source',)
    list_filter = ('source',)
    search_fields = ('title',)
    readonly_fields = ('uid',)
    date_hierarchy = 'published_at'


class FeedSourceInline(admin.TabularInline):
    model = FeedSource
    extra = 0
    fields = ('source', 'name', 'enabled', 'order')
    autocomplete_fields = ('source',)


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'order')
    list_select_related = ('user',)
    list_filter = ('user',)
    search_fields = ('name', 'user__email')
    autocomplete_fields = ('user',)
    readonly_fields = ('uid',)
    inlines = (FeedSourceInline,)


class OwnedByUserAdmin(admin.ModelAdmin):
    """Registered, but not listed on the admin index.

    Saved posts belong to one account, so the user's own page is where they are edited. They
    still need registering — the saved pile needs a changelist to link to once it outgrows a
    form. `get_model_perms` returning
    empty drops the model from the index while leaving those URLs working, which is the one
    supported way to have exactly that.
    """

    def get_model_perms(self, request):
        return {}


@admin.register(SavedPost)
class SavedPostAdmin(OwnedByUserAdmin):
    list_display = ('user', 'post', 'group', 'saved_at')
    list_select_related = ('user', 'post')
    list_filter = ('group', 'user')
    autocomplete_fields = ('user', 'post')


# UserSettings is deliberately not registered on its own: it is one row per account with
# nothing to list across accounts, and UserSettingsInline edits it in place on the user.
