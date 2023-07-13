django-auditlog
===============

[![Jazzband](https://jazzband.co/static/img/badge.svg)](https://jazzband.co/)
[![Build Status](https://github.com/jazzband/django-auditlog/workflows/Test/badge.svg)](https://github.com/jazzband/django-auditlog/actions)
[![Docs](https://readthedocs.org/projects/django-auditlog/badge/?version=latest)](https://django-auditlog.readthedocs.org/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/jazzband/django-auditlog/branch/master/graph/badge.svg)](https://codecov.io/gh/jazzband/django-auditlog)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/django-auditlog.svg)](https://pypi.python.org/pypi/django-auditlog)
[![Supported Django versions](https://img.shields.io/pypi/djversions/django-auditlog.svg)](https://pypi.python.org/pypi/django-auditlog)

```django-auditlog``` (Auditlog) is a reusable app for Django that makes logging object changes a breeze. Auditlog tries to use as much as Python and Django's built in functionality to keep the list of dependencies as short as possible. Also, Auditlog aims to be fast and simple to use.

Auditlog is created out of the need for a simple Django app that logs changes to models along with the user who made the changes (later referred to as actor). Existing solutions seemed to offer a type of version control, which was found excessive and expensive in terms of database storage and performance.

The core idea of Auditlog is similar to the log from Django's admin. Unlike the log from Django's admin (```django.contrib.admin```) Auditlog is much more flexible. Also, Auditlog saves a summary of the changes in JSON format, so changes can be tracked easily.

Documentation
-------------

The documentation for ```django-auditlog``` can be found on https://django-auditlog.readthedocs.org. The source files are available in the ```docs``` folder.

License
-------

Auditlog is licensed under the MIT license (see the ```LICENSE``` file for details).

Contribute
----------

If you have great ideas for Auditlog, or if you like to improve something, feel free to fork this repository and/or create a pull request. I'm open for suggestions. If you like to discuss something with me (about Auditlog), please open an issue.

Releases
--------

1. Make sure all tests on `master` are green
2. Create a new branch `vX.Y.Z` from master for that specific release
3. Update the CHANGELOG release date
4. Pull request `vX.Y.Z` -> `master`
5. As a project lead, once the PR is merged, create and push a tag `vX.Y.Z`: this will trigger the release build and a notification will be sent from Jazzband of the availability of two packages (tgz and wheel)
6. Test the install
7. Publish the release to PyPI
