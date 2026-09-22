from functools import partial

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models.functions import Upper
from django.utils import timezone

from .uids import make_uid

# The text-search dictionary Post.search is generated with. core/search.py reads it from
# here rather than declaring its own: the column is the authoritative one, and a query that
# stems with a different dictionary than the column was built with silently matches nothing.
SEARCH_CONFIG = 'english'


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('email is required')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        # password=None → unusable password: app users sign in with Google only
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    google_sub = models.CharField(max_length=64, unique=True, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email


class AuthToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens')
    token_hash = models.CharField(max_length=64, unique=True)
    device_label = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # default= rather than auto_now_add=: the sliding window is measured from this
    # field, so BearerAuth has to be able to write it. See core/auth.py.
    last_used_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user} · {self.device_label or "unknown device"}'


class Source(models.Model):
    class Type(models.TextChoices):
        WEBSITE = 'website'
        YOUTUBE = 'youtube'
        REDDIT = 'reddit'

    uid = models.CharField(max_length=32, unique=True, default=partial(make_uid, 'source_'))
    type = models.CharField(max_length=10, choices=Type.choices)
    feed_url = models.URLField(max_length=500, unique=True)
    site_url = models.URLField(max_length=500, blank=True)
    title = models.CharField(max_length=300, blank=True)
    icon_url = models.URLField(max_length=500, blank=True)
    active = models.BooleanField(default=True)
    # etag / last_modified are opaque HTTP header values for conditional GETs
    etag = models.CharField(max_length=200, blank=True)
    last_modified = models.CharField(max_length=100, blank=True)
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    next_fetch_at = models.DateTimeField(null=True, blank=True)
    error_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title or self.feed_url


class Post(models.Model):
    uid = models.CharField(max_length=32, unique=True, default=partial(make_uid, 'post_'))
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='posts')
    guid = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    post_url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1000, blank=True)
    summary = models.TextField(blank=True)
    # null = not yet extracted; filled globally on first /posts/{uid}/article request.
    # Distinct from '' (extraction ran, found nothing), so DJ001's two-empty-values
    # objection doesn't apply.
    article_html = models.TextField(null=True, blank=True)  # noqa: DJ001
    published_at = models.DateTimeField()
    # Maintained by Postgres, not by us: a persisted generated column is recomputed in the
    # same statement that writes the row, so search can never be stale and there is no sync
    # pipeline to run. db_persist isn't a choice — Postgres only implements STORED. Legal
    # inside a generated expression only because the two-argument to_tsvector() Django emits
    # for an explicit `config` is IMMUTABLE; the one-argument form would be rejected.
    # Title outweighs summary so a later switch to rank ordering needs no migration.
    search = models.GeneratedField(
        expression=SearchVector('title', weight='A', config=SEARCH_CONFIG)
        + SearchVector('summary', weight='B', config=SEARCH_CONFIG),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['source', 'guid'], name='unique_post_guid_per_source'),
        ]
        indexes = [
            models.Index(fields=['source', '-published_at']),
            GinIndex(fields=['search'], name='post_search_gin'),
            # Functional, not a plain index on `title`: Django compiles __icontains to
            # UPPER("title"::text) LIKE UPPER(%s) (postgresql/operations.py lookup_cast), and
            # the planner only matches an index whose expression is the same one. This is the
            # half that answers partial words ("rout" -> "router"), which FTS's whole-word
            # tokens structurally cannot.
            GinIndex(OpClass(Upper('title'), name='gin_trgm_ops'), name='post_title_trgm'),
        ]

    def __str__(self):
        return self.title


class Feed(models.Model):
    uid = models.CharField(max_length=32, unique=True, default=partial(make_uid, 'feed_'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feeds')
    # sources are only deleted by orphan cleanup, which checks for feeds first
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name='feeds')
    name = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'source'], name='unique_feed_per_user_source'),
        ]
        ordering = ['order']

    def __str__(self):
        return self.name


class Folder(models.Model):
    uid = models.CharField(max_length=32, unique=True, default=partial(make_uid, 'folder_'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)
    feeds = models.ManyToManyField(Feed, through='FolderMember', related_name='folders')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class FolderMember(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='members')
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='memberships')
    muted = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['folder', 'feed'], name='unique_member_per_folder'),
        ]
        ordering = ['order']

    def __str__(self):
        return f'{self.folder} · {self.feed}'


class SavedPost(models.Model):
    class Group(models.TextChoices):
        BOOKMARKS = 'bookmarks'
        FAVORITES = 'favorites'
        LATER = 'later'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saves')
    group = models.CharField(max_length=10, choices=Group.choices)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # a post lives in exactly one group per user; moving groups is an upsert
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_saved_post_per_user'),
        ]

    def __str__(self):
        return f'{self.post} · {self.group}'


class UserSettings(models.Model):
    class Theme(models.TextChoices):
        INK = 'ink'
        CLAUDE = 'claude'

    class FeedListStyle(models.TextChoices):
        LIST = 'list'
        CARDS = 'cards'

    class ScrollbarStyle(models.TextChoices):
        THIN = 'thin'
        COMFORTABLE = 'comfortable'
        # the Appearance panel calls this one "System" — it writes no scrollbar rules at all
        AUTO = 'auto', 'System'

    class PostCardStyle(models.TextChoices):
        # a 16:9 image on top, or date + title alone. A post with no image renders compact
        # under either (docs/images.md § Rendering).
        IMAGE = 'image'
        COMPACT = 'compact'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.INK)
    feed_list_style = models.CharField(
        max_length=10, choices=FeedListStyle.choices, default=FeedListStyle.LIST
    )
    scrollbar_style = models.CharField(
        max_length=11, choices=ScrollbarStyle.choices, default=ScrollbarStyle.THIN
    )
    post_card_style = models.CharField(
        max_length=7, choices=PostCardStyle.choices, default=PostCardStyle.IMAGE
    )

    class Meta:
        verbose_name_plural = 'user settings'

    def __str__(self):
        return f'settings for {self.user}'
