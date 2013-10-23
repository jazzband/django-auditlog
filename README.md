django-auditlog
===============

**Please remember that this app is still in development and not yet suitable for production environments.**

```django-auditlog``` (Auditlog) is created out of the need for a simple Django app that logs changes to models, including the user that changed the models. Some requirements were that the overhead had to be low and that the app should be able to handle high volumes of log entries. Full-blown version control (with functionalities like reverting changes) was not needed, and would cause too much overhead. After looking for some time I did not find an app like that.

Auditlog provides a log of changes made to a model instance. It also saves the user that made the changes (only when changes were made in a request). Unlike the log from Django's admin (```django.contrib.admin```) Auditlog also saves a summary of the changes in JSON format, so changes can be tracked easily and the right people can be blamed for unwanted changes.

Installation
------------

The easiest way to install Auditlog is from PyPI (https://pypi.python.org/pypi/django-auditlog/). If you have ```pip``` installed, you can simply run the following command:

```pip install django-auditlog```

You can also clone the git repository (or download the zipped files) and run ```setup.py``` or copy the ```src/auditlog``` directory into your Django project.

You can enable Auditlog by simply adding ```'auditlog'``` to your ```INSTALLED_APPS``` setting in your project's ```settings.py``` file.

If you want your log entries to automatically contain the actor, you also need to add ```'auditlog.middleware.AuditLogMiddleware'``` to the ```MIDDLEWARE_CLASSES``` setting in the same file.

Usage
-----

For the features below to work, you need to add the following imports to the top of the ```models.py``` file.

```python
from auditlog.models import AuditLogHistoryField
from auditlog.registry import auditlog
```

Before Auditlog logs mutations on model instances, each model must be registered. This can be done by adding the following line of code to the ```models.py``` file (below the model itself). Change ```MyModel``` to the model you want to register.

```python
auditlog.register(MyModel)
```

It is possible to have a model instances history directly available through a custom field. For this, you can add the following code to a subclass of ```models.Model```:

```python
history = AuditLogHistoryField()
```

Note that use of the field is not required for Auditlog to work, it is just a shortcut to get the log entries easier. Also, registering the model is not required for the field to work. This allows you to keep access to log entries once logging is no longer needed and you can add it to an abstract model without implicitly registering all subclasses of that model for logging.

License
-------

Auditlog is licensed under the MIT license (see the ```LICENSE``` file for details).

Contribute
----------

If you have great ideas for Auditlog, or if you like to improve something, feel free to fork this repository and/or create a pull request. I'm open for suggestions. If you like to discuss something with me (about Auditlog), please open an issue.
