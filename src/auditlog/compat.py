import django

def is_authenticated(user):
    """Return whether or not a User is authenticated.

    Function provides compatibility following deprecation of method call to
    `is_authenticated()` in Django 2.0.

    This is *only* required to support Django < v1.10 (i.e. v1.9 and earlier),
    as `is_authenticated` was introduced as a property in v1.10.s
    """
    if not hasattr(user, 'is_authenticated'):
       return False
    if callable(user.is_authenticated):
        # Will be callable if django.version < 2.0, but is only necessary in
        # v1.9 and earlier due to change introduced in v1.10 making
        # `is_authenticated` a property instead of a callable.
        return user.is_authenticated()
    else:
        return user.is_authenticated
