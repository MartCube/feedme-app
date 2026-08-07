import secrets
import string

ALPHABET = string.digits + string.ascii_letters


def make_uid(prefix):
    """Mint a public uid: prefix + 12 random base62 chars (e.g. 'feed_a1B2c3D4e5F6').

    The backend mints every public uid with the prefixes the frontend resolves
    (docs/backend.md § Vocabulary). Use via functools.partial in model defaults.
    """
    return prefix + ''.join(secrets.choice(ALPHABET) for _ in range(12))
