Usage
=====

Automatically logging changes
-----------------------------

Auditlog can automatically log changes to objects for you. This functionality is based on Django's signals, but linking
your models to Auditlog is even easier than using signals.

Registering your model for logging can be done with a single line of code, as the following example illustrates::

    from auditlog.registry import auditlog
    from django.db import models

    class MyModel(models.Model):
        pass
        # Model definition goes here

    auditlog.register(MyModel)

It is recommended to place the register code (``auditlog.register(MyModel)``) at the bottom of your ``models.py`` file.
This ensures that every time your model is imported it will also be registered to log changes. Auditlog makes sure that
each model is only registered once, otherwise duplicate log entries would occur.

**Excluding fields**

Fields that are excluded will not trigger saving a new log entry and will not show up in the recorded changes.

To exclude specific fields from the log you can pass ``include_fields`` resp. ``exclude_fields`` to the ``register``
method. If ``exclude_fields`` is specified the fields with the given names will not be included in the generated log
entries. If ``include_fields`` is specified only the fields with the given names will be included in the generated log
entries. Explicitly excluding fields through ``exclude_fields`` takes precedence over specifying which fields to
include.

For example, to exclude the field ``last_updated``, use::

    auditlog.register(MyModel, exclude_fields=['last_updated'])

.. versionadded:: 0.3.0

    Excluding fields

Actors
------

When using automatic logging, the actor is empty by default. However, auditlog can set the actor from the current
request automatically. This does not need any custom code, adding a middleware class is enough.

To enable the automatic logging of the actors, simply add the following to your ``MIDDLEWARE_CLASSES`` setting in your
project's configuration file::

    MIDDLEWARE_CLASSES = (
        # Request altering middleware, e.g., Django's default middleware classes
        'auditlog.middleware.AuditlogMiddleware',
        # Other middleware
    )

It is recommended to keep all middleware that alters the request loaded before Auditlog's middleware.

.. warning::

    Please keep in mind that every object change in a request that gets logged automatically will have the current request's
    user as actor. To only have some object changes to be logged with the current request's user as actor manual logging is
    required.

Object history
--------------

.. py:currentmodule:: auditlog.models

Auditlog ships with a custom field that enables you to easily get the log entries that are relevant to your object. This
functionality is built on Django's content types framework (``django.contrib.contenttypes``). Using this field in your
models is equally easy as any other field::

    from auditlog.models import AuditlogHistoryField
    from auditlog.registry import auditlog
    from django.db import models

    class MyModel(models.Model):
        history = AuditlogHistoryField()
        # Model definition goes here

    auditlog.register(MyModel)

:py:class:`AuditlogHistoryField` accepts an optional :py:attr:`pk_indexable` parameter, which is either ``True`` or
``False``, this defaults to ``True``. If your model has a custom primary key that is not an integer value,
:py:attr:`pk_indexable` needs to be set to ``False``. Keep in mind that this might slow down queries.
