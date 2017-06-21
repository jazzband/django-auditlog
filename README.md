agfunder/django-auditlog
===============

This fork adds some key improvements we needed to completely track changes in our models:

- tracking m2m field changes (see https://docs.djangoproject.com/en/1.11/ref/signals/#m2m-changed)
- tracking mptt tree structure changes (see https://github.com/django-mptt/django-mptt/blob/master/mptt/signals.py)
- eliminating spurious changes of saving empty fields turning NULL into blank string (see https://code.djangoproject.com/ticket/9590)
- improving admin view
- tracking additional parameters in additional_data

Note m2m and mptt tracking results in additional logentry rows.  Because django emits separate signals for model, m2m, and mptt structure changes, we did not see a straighforward way to combine these into a single logentry row.

### tracking m2m
- currently requires specifically naming each m2m field to be tracked
- stores human-readable changes in "changes" field.  This shows string representation of child table rows added and removed.
- stores JSON representation of changes in "additional data" field.  This includes ids child table rows added and removed.
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
- currently requires specifically naming each mptt field to be tracked
- stores human-readable changes in "changes" field.  This shows string representation of node parent before and after moving the mptt node.
- stores JSON representation of changes in "additional data" field.  This includes ids of node parent before and after moving the mptt node.
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
- "changes" field is human-friendly format, whereas "additional_data" field is machine-readable format

### integration with django admin change_form UI
- we manually replaced change_form.html for models which used auditlog, so HISTORY button was replaced by a specially crafted AUDITLOG link into the auditlog logentry changeset `/admin/auditlog/logentry?q={{ original.uuid }}`
- for each model tracked with auditlog, we:
    - had a uuid field `uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)`
    - inserted the uuid with `get_additional_data()`, which auditlog uses to populate additional_data field
    - added additional_data to admin search for auditlog
- the result was that AUDITLOG link (using uuid parameter) showed a complete list of auditlog entries for the specific object

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
