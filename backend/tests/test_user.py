def test_user_fixture_persists(user):
    """Also proves pytest-django can build the test database against our custom User model."""
    assert user.pk is not None
    assert user.email == 'reader@example.com'
    assert not user.has_usable_password()
