django-auditlog
===============

[![Build Status](https://travis-ci.org/jjkester/django-auditlog.svg?branch=master)](https://travis-ci.org/jjkester/django-auditlog)
[![Docs](https://readthedocs.org/projects/django-auditlog/badge/?version=latest)](http://django-auditlog.readthedocs.org/en/latest/?badge=latest)

**Please remember that this app is still in development.**
**Test this app before deploying it in production environments.**

```django-auditlog``` (Auditlog) is a reusable app for Django that makes logging object changes a breeze. Auditlog tries to use as much as Python and Django’s built in functionality to keep the list of dependencies as short as possible. Also, Auditlog aims to be fast and simple to use.

Auditlog is created out of the need for a simple Django app that logs changes to models along with the user who made the changes (later referred to as actor). Existing solutions seemed to offer a type of version control, which was found excessive and expensive in terms of database storage and performance.

The core idea of Auditlog is similar to the log from Django’s admin. Unlike the log from Django’s admin (```django.contrib.admin```) Auditlog is much more flexible. Also, Auditlog saves a summary of the changes in JSON format, so changes can be tracked easily.

Documentation
-------------

The documentation for ```django-auditlog``` can be found on http://django-auditlog.readthedocs.org. The source files are available in the ```docs``` folder.

License
-------

Auditlog is licensed under the MIT license (see the ```LICENSE``` file for details).

Contribute
----------

If you have great ideas for Auditlog, or if you like to improve something, feel free to fork this repository and/or create a pull request. I'm open for suggestions. If you like to discuss something with me (about Auditlog), please open an issue.

Releases
--------

1. Make sure all tests on `master` are green.
2. Create a new branch `vX.Y.Z` from master for that specific release.
3. Bump versions in `setup.py` and `docs/source/conf.py` (docs have 2 places where the versions need to be changed!)
4. Pull request `vX.Y.Z` -> `stable`. Merging policy is very strict. This triggers a new release.
5. Pull request `stable` -> `master`. Now everything is back in sync.

Opening a pull request from `master` directly to `stable` is discouraged as `master` may be updated while the PR is open, thus changing the contents of the release.

