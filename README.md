*Since my time is very, very limited at the moment and my personal need for the functionality provided by django-auditlog has gone development might be very slow. However, I am happy to look at pull requests for issues. If you like to be a permanent contributor, please contact me (janjelle [at] jjkester [dot] nl).*

django-auditlog
===============

[![Build Status](https://travis-ci.org/jjkester/django-auditlog.svg?branch=master)](https://travis-ci.org/jjkester/django-auditlog)

**Please remember that this app is still in development and not yet suitable for production environments.**

```django-auditlog``` (Auditlog) is a reusable app for Django that makes logging object changes a breeze. Auditlog tries to use as much as Python and Django’s built in functionality to keep the list of dependencies as short as possible. Also, Auditlog aims to be fast and simple to use.

Auditlog is created out of the need for a simple Django app that logs changes to models, including the user that changed the models (later referred to as actor). Existing solutions seemed to offer a type of version control, which was not needed and would cause too much overhead.

The core idea of Auditlog is similar to the log from Django’s admin. Unlike the log from Django’s admin (django.contrib.admin) Auditlog is much more flexible and also saves a summary of the changes in JSON format, so changes can be tracked easily.

Documentation
-------------

The documentation for ``django-auditlog`` can be found on http://django-auditlog.readthedocs.org.

License
-------

Auditlog is licensed under the MIT license (see the ```LICENSE``` file for details).

Contribute
----------

If you have great ideas for Auditlog, or if you like to improve something, feel free to fork this repository and/or create a pull request. I'm open for suggestions. If you like to discuss something with me (about Auditlog), please open an issue.
