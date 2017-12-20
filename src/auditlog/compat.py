import django

def is_authenticated(user):
    """
    Return whether or not a User is authenticated.

    Function provides compatibility following deprecation of method call to
    is_authenticated() in Django 2.0.
    """
    if not hasattr(user, 'is_authenticated'):
        return False
    if hasattr(user.is_authenticated, "__call__"):
        return user.is_authenticated()
    else:
        return user.is_authenticated
