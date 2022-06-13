Usage
=====

.. py:currentmodule:: auditlog.models

Manually logging changes
------------------------

Auditlog log entries are simple :py:class:`LogEntry` model instances. This makes creating a new log entry very easy. For
even more convenience, :py:class:`LogEntryManager` provides a number of methods which take some work out of your hands.

See :doc:`internals` for all details.

.. _Automatically logging changes:

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

**Mapping fields**

If you have field names on your models that aren't intuitive or user friendly you can include a dictionary of field mappings
during the `register()` call.

.. code-block:: python

    class MyModel(modelsModel):
        sku = models.CharField(max_length=20)
        version = models.CharField(max_length=5)
        product = models.CharField(max_length=50, verbose_name='Product Name')
        history = AuditlogHistoryField()

    auditlog.register(MyModel, mapping_fields={'sku': 'Product No.', 'version': 'Product Revision'})

.. code-block:: python

    log = MyModel.objects.first().history.latest()
    log.changes_display_dict
    // retrieves changes with keys Product No. Product Revision, and Product Name
    // If you don't map a field it will fall back on the verbose_name

.. versionadded:: 0.5.0

You do not need to map all the fields of the model, any fields not mapped will fall back on their ``verbose_name``. Django provides a default ``verbose_name`` which is a "munged camel case version" so ``product_name`` would become ``Product Name`` by default.

**Masking fields**

Fields that contain sensitive info and we want keep track of field change but not to contain the exact change.

To mask specific fields from the log you can pass ``mask_fields`` to the ``register``
method. If ``mask_fields`` is specified, the first half value of the fields is masked using ``*``.

For example, to mask the field ``address``, use::

    auditlog.register(MyModel, mask_fields=['address'])

.. versionadded:: 2.0.0

    Masking fields

**Many-to-many fields**

Changes to many-to-many fields are not tracked by default. If you want to enable tracking of a many-to-many field on a model, pass ``m2m_fields`` to the ``register`` method:

.. code-block:: python

    auditlog.register(MyModel, m2m_fields={"tags", "contacts"})

This functionality is based on the ``m2m_changed`` signal sent by the ``through`` model of the relationship.

Note that when the user changes multiple many-to-many fields on the same object through the admin, both adding and removing some objects from each, this code will generate multiple log entries: each log entry will represent a single operation (add or delete) of a single field, e.g. if you both add and delete values from 2 fields on the same form in the same request, you'll get 4 log entries.

.. versionadded:: 2.1.0

Settings
--------

**AUDITLOG_INCLUDE_ALL_MODELS**

You can use this setting to register all your models:

.. code-block:: python

    AUDITLOG_INCLUDE_ALL_MODELS=True

.. versionadded:: 2.1.0

**AUDITLOG_EXCLUDE_TRACKING_MODELS**

You can use this setting to exclude models in registration process.
It will be considered when ``AUDITLOG_INCLUDE_ALL_MODELS`` is `True`.

.. code-block:: python

    AUDITLOG_EXCLUDE_TRACKING_MODELS = (
        "<app_name>",
        "<app_name>.<model>"
    )

.. versionadded:: 2.1.0

**AUDITLOG_INCLUDE_TRACKING_MODELS**

You can use this setting to configure your models registration and other behaviours.
It must be a list or tuple. Each item in this setting can be a:

* ``str``: To register a model.
* ``dict``: To register a model and define its logging behaviour. e.g. include_fields, exclude_fields.

.. code-block:: python

    AUDITLOG_INCLUDE_TRACKING_MODELS = (
        "<appname>.<model1>",
        {
            "model": "<appname>.<model1>",
            "include_fields": ["field1", "field2"],
            "exclude_fields": ["field3", "field4"],
            "mapping_fields": {
                "field1": "FIELD",
            },
            "mask_fields": ["field5", "field6"],
            "m2m_fields": ["field7", "field8"],
        },
        "<appname>.<model3>",
    )

.. versionadded:: 2.1.0

Actors
------

Middleware
**********

When using automatic logging, the actor is empty by default. However, auditlog can set the actor from the current
request automatically. This does not need any custom code, adding a middleware class is enough. When an actor is logged
the remote address of that actor will be logged as well.

To enable the automatic logging of the actors, simply add the following to your ``MIDDLEWARE`` setting in your
project's configuration file::

    MIDDLEWARE = (
        # Request altering middleware, e.g., Django's default middleware classes
        'auditlog.middleware.AuditlogMiddleware',
        # Other middleware
    )

It is recommended to keep all middleware that alters the request loaded before Auditlog's middleware.

.. warning::

    Please keep in mind that every object change in a request that gets logged automatically will have the current request's
    user as actor. To only have some object changes to be logged with the current request's user as actor manual logging is
    required.

Context manager
***************

.. versionadded:: 2.1.0

To enable the automatic logging of the actors outside of request context (e.g. in a Celery task), you can use a context
manager::

    from auditlog.context import set_actor

    def do_stuff(actor_id: int):
        actor = get_user(actor_id)
        with set_actor(actor):
            # if your code here leads to creation of LogEntry instances, these will have the actor set
            ...

Object history
--------------

Auditlog ships with a custom field that enables you to easily get the log entries that are relevant to your object. This
functionality is built on Django's content types framework (:py:mod:`django.contrib.contenttypes`). Using this field in
your models is equally easy as any other field::

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

The :py:class:`AuditlogHistoryField` provides easy access to :py:class:`LogEntry` instances related to the model instance. Here is an example of how to use it:

.. code-block:: html

    <div class="table-responsive">
      <table class="table table-striped table-bordered">
        <thead>
          <tr>
            <th>Field</th>
            <th>From</th>
            <th>To</th>
          </tr>
        </thead>
        <tbody>
        {% for key, value in mymodel.history.latest.changes_dict.items %}
          <tr>
            <td>{{ key }}</td>
            <td>{{ value.0|default:"None" }}</td>
            <td>{{ value.1|default:"None" }}</td>
          </tr>
        {% empty %}
          <p>No history for this item has been logged yet.</p>
        {% endfor %}
        </tbody>
      </table>
    </div>

If you want to display the changes in a more human readable format use the :py:class:`LogEntry`'s :py:attr:`changes_display_dict` instead. The :py:attr:`changes_display_dict` will make a few cosmetic changes to the data.

- Mapping Fields property will be used to display field names, falling back on ``verbose_name`` if no mapping field is present
- Fields with a value whose length is greater than 140 will be truncated with an ellipsis appended
- Date, Time, and DateTime fields will follow ``L10N`` formatting. If ``USE_L10N=False`` in your settings it will fall back on the settings defaults defined for ``DATE_FORMAT``, ``TIME_FORMAT``, and ``DATETIME_FORMAT``
- Fields with ``choices`` will be translated into their human readable form, this feature also supports choices defined on ``django-multiselectfield`` and Postgres's native ``ArrayField``

Check out the internals for the full list of attributes you can use to get associated :py:class:`LogEntry` instances.

Many-to-many relationships
--------------------------

.. versionadded:: 0.3.0

.. note::

    This section shows a workaround which can be used to track many-to-many relationships on older versions of django-auditlog. For versions 2.1.0 and onwards, please see the many-to-many fields section of :ref:`Automatically logging changes`.
    **Do not rely on the workaround here to be stable across releases.**

By default, many-to-many relationships are not tracked by Auditlog.

The history for a many-to-many relationship without an explicit 'through' model can be recorded by registering this
model as follows::

    auditlog.register(MyModel.related.through)

The log entries for all instances of the 'through' model that are related to a ``MyModel`` instance can be retrieved
with the :py:meth:`LogEntryManager.get_for_objects` method. The resulting QuerySet can be combined with any other
queryset of :py:class:`LogEntry` instances. This way it is possible to get a list of all changes on an object and its
related objects::

    obj = MyModel.objects.first()
    rel_history = LogEntry.objects.get_for_objects(obj.related.all())
    full_history = (obj.history.all() | rel_history.all()).order_by('-timestamp')

Management commands
-------------------

.. versionadded:: 0.4.0

Auditlog provides the ``auditlogflush`` management command to clear all log entries from the database.

By default, the command asks for confirmation. It is possible to run the command with the ``-y`` or ``--yes`` flag to skip
confirmation and immediately delete all entries.

You may also specify a date using the ``-b`` or ``--before-date`` option in ISO 8601 format (YYYY-mm-dd) to delete all
log entries prior to a given date. This may be used to implement time based retention windows.

.. versionadded:: 2.1.0

.. warning::

    Using the ``auditlogflush`` command deletes log entries permanently and irreversibly from the database.

Django Admin integration
------------------------

.. versionadded:: 0.4.1

When ``auditlog`` is added to your ``INSTALLED_APPS`` setting a customized admin class is active providing an enhanced
Django Admin interface for log entries.
