Troubleshooting
===============

Users removing their own account
--------------------------------

When using the middleware to automatically logging changes and implementing a functionality so that users
can remove their own account, auditlog will try to set the actor of the change to the user that is
being removed, raising a database IntegrityError exception.

This can be workarounded by unregistering the model that you are trying to remove and registering it back
again.

.. code-block:: python

    def remove_account(request):
        auditlog.unregister(User)
        request.user.delete()
        auditlog.register(User)
