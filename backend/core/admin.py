from django.contrib import admin

from .models import AuthToken, Feed, Folder, FolderMember, Post, SavedPost, Source, User, UserSettings


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'google_sub', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email',)
    # password is a hash — managed by createsuperuser / ensure_superuser, not edited raw
    exclude = ('password',)
    readonly_fields = ('created_at', 'last_login')


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_label', 'created_at', 'last_used_at')
    search_fields = ('user__email',)
    readonly_fields = ('token_hash', 'created_at', 'last_used_at')


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'active', 'error_count', 'last_fetched_at', 'next_fetch_at', 'feed_url')
    list_filter = ('type', 'active')
    search_fields = ('title', 'feed_url', 'site_url')
    readonly_fields = ('uid',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_at')
    list_select_related = ('source',)
    search_fields = ('title',)
    readonly_fields = ('uid',)
    date_hierarchy = 'published_at'


class FolderMemberInline(admin.TabularInline):
    model = FolderMember
    extra = 0


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'source', 'order')
    list_select_related = ('user', 'source')
    search_fields = ('name', 'user__email')
    readonly_fields = ('uid',)


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'order')
    list_select_related = ('user',)
    search_fields = ('name', 'user__email')
    readonly_fields = ('uid',)
    inlines = (FolderMemberInline,)


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'group', 'saved_at')
    list_select_related = ('user', 'post')
    list_filter = ('group',)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'feed_list_style')
