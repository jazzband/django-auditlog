django-auditlog
===============

# agfunder/django-auditlog

This fork adds some key improvements we needed to completely track changes in our models:

- tracking m2m field changes
- tracking mptt tree structure changes
- improving admin view
- tracking additional parameters in additional_data

Note m2m and mptt tracking results in additional logentry rows.  Because django emits separate signals for model, m2m, and mptt structure changes, we did not see a straighforward way to combine these into a single logentry row.

### tracking m2m
```
from auditlog.registry_ext import auditlog_register_m2m

class Category(models.Model):
    name = CharField(max_length=30, null=True)

class Blog(models.Model):
    categories = ManyToManyField(Category, null=True)

auditlog.register(Blog)
auditlog_register_m2m(Blog.categories)
```

### tracking mptt
```
from auditlog.registry_ext import auditlog_register_mptt
from model_utils import FieldTracker

class MyTree(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    tracker = FieldTracker()

auditlog.register(MyTree)
auditlog_register_mptt(MyTree.parent)
```

### additional_data
- we assume additional_data is a dict (to store in JSON format)
- m2m and mptt handlers stuff additional fields into additional_data
- changes field is human-friendly format, whereas additional_data is machine-readable format

Upstream repo README continues below:

---------


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
