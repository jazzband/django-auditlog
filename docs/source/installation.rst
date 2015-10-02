Installation
============

Installing Auditlog is simple and straightforward. First of all, you need a copy of Auditlog on your system. The easiest
way to do this is by using the Python Package Index (PyPI). Simply run the following command:

``pip install django-auditlog``

Instead of installing Auditlog via PyPI, you can also clone the Git repository or download the source code via GitHub.
The repository can be found at https://github.com/jjkester/django-auditlog/.

**Requirements**

- Python 2.7 or 3.4
- Django 1.7 or 1.8

Auditlog is currently tested with Python 2.7 and 3.4 and Django 1.7 and 1.8. The test report can be found at
https://travis-ci.org/jjkester/django-auditlog.

Adding Auditlog to your Django application
------------------------------------------

To use Auditlog in your application, just add ``'auditlog'`` to your project's ``INSTALLED_APPS`` setting and run
``manage.py migrate`` to create/upgrade the necessary database structure.

If you want Auditlog to automatically set the actor for log entries you also need to enable the middleware by adding
``'auditlog.middleware.AuditlogMiddleware'`` to your ``MIDDLEWARE_CLASSES`` setting.
