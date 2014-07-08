Internals
=========

You might be interested in the way things work on the inside of Auditlog. This section covers the internal APIs of
Auditlog which is very useful when you are looking for more advanced ways to use the application or if you like to
contribute to the project.

The documentation below is automatically generated from the source code.

Models and fields
-----------------

.. automodule:: auditlog.models
    :members: LogEntry, LogEntryManager, AuditlogHistoryField

Middleware
----------

.. automodule:: auditlog.middleware
    :members: AuditlogMiddleware

Signal receivers
----------------

.. automodule:: auditlog.receivers
    :members:

Calculating changes
-------------------

.. automodule:: auditlog.diff
    :members:

Registry
--------

.. automodule:: auditlog.registry
    :members:
