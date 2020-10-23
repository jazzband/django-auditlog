django-auditlog documentation
=============================

django-auditlog (Auditlog) is a reusable app for Django that makes logging object changes a breeze. Auditlog tries to
use as much as Python and Django's built in functionality to keep the list of dependencies as short as possible. Also,
Auditlog aims to be fast and simple to use.

Auditlog is created out of the need for a simple Django app that logs changes to models along with the user who made the
changes (later referred to as actor). Existing solutions seemed to offer a type of version control, which was found
excessive and expensive in terms of database storage and performance.

The core idea of Auditlog is similar to the log from Django's admin. However, Auditlog is much more flexible than the
log from Django's admin app (:py:mod:`django.contrib.admin`). Also, Auditlog saves a summary of the changes in JSON
format, so changes can be tracked easily.

Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   usage
   internals


Contribute to Auditlog
----------------------

.. note::
   Due to multiple reasons the development of Auditlog is not a priority for me at this moment. Therefore progress might
   be slow. This does not mean that this project is abandoned! Community involvement in the form of pull requests is
   very much appreciated. Also, if you like to take Auditlog to the next level and be a permanent contributor, please
   contact the author. Contact information can be found via GitHub.

If you discovered a bug or want to improve the code, please submit an issue and/or pull request via GitHub.
Before submitting a new issue, please make sure there is no issue submitted that involves the same problem.

| GitHub repository: https://github.com/jazzband/django-auditlog
| Issues: https://github.com/jazzband/django-auditlog/issues
