# Changes

#### Fixes

- Fix inconsistent changes with JSONField ([#355](https://github.com/jazzband/django-auditlog/pull/355))

## 2.0.0 (2022-05-09)

#### Improvements
- feat: enable use of replica database (delegating the choice to `DATABASES_ROUTER`) ([#359](https://github.com/jazzband/django-auditlog/pull/359))
- Add `mask_fields` argument in `register` to mask sensitive information when logging ([#310](https://github.com/jazzband/django-auditlog/pull/310))
- Django: Drop 2.2 support. `django_jsonfield_backport` is not required anymore ([#370](https://github.com/jazzband/django-auditlog/pull/370))
- Remove `default_app_config` configuration ([#372](https://github.com/jazzband/django-auditlog/pull/372))

#### Important notes
- LogEntry no longer save to same database instance is using

## 1.0.0 (2022-01-24)

### Final

#### Improvements

- build: add classifiers for Python and Django
- build: replace django-jsonfield with django-jsonfield-backport ([#339](https://github.com/jazzband/django-auditlog/pull/339))
- ci: replace Travis with Github Actions
- docs: follow Jazzband guidelines (badge, how to contribute, code of conduct) ([#269](https://github.com/jazzband/django-auditlog/pull/269))
- docs: add a changelog
- docs: remove note about maintenance
- docs: update the release strategy
- docs: use the latest django LTS (3.2) to build docs
- feat: add a db index to `LogEntry`'s `action` field ([#236](https://github.com/jazzband/django-auditlog/pull/236))
- feat: add the content type to `resource` field
- feat: add the `actor` username to search fields in admin
- refactor: lint the code with Black and isort
- tests: init pre-commit config
- Python: add 3.9 and 3.10 support, drop 3.5 and 3.6 support
- Django: add 3.2 (LTS) and 4.0 support, drop 3.0 and 3.1 support

#### Fixes

- docs: replace `MIDDLEWARE_CLASSES` with `MIDDLEWARE`
- Remove old django (< 1.9) related codes
- Replace deprecated `smart_text()` with `smart_str()`
- Replace `ugettext` with `gettext` for Django 4
- Support Django's save method `update_fields` kwarg ([#336](https://github.com/jazzband/django-auditlog/pull/336))
- Fix invalid escape sequence on Python 3.7


### Alpha 1 (1.0a1, 2020-09-07)

#### Improvements

- Refactor the `auditlogflush` management command
- Clean up project structure
- Python: add 3.8 support, drop 2.7 and 3.4 support
- Django: add 3.0 and 3.1 support, drop 1.11, 2.0 and 2.1 support

#### Fixes

- Fix field choices diff
- Allow higher versions of python-dateutil than 2.6.0


## 0.4.8 (2019-11-12)

### Improvements

- Add support for PostgreSQL 10


## 0.4.7 (2019-12-19)

### Improvements

- Improve support multiple database (PostgreSQL, MySQL)
- Django: add 2.1 and 2.2 support, drop < 1.11 versions
- Python: add 3.7 support


## 0.4.6 (2018-09-18)

### Features

- Allow `AuditlogHistoryField` to block cascading deletes ([#172](https://github.com/jazzband/django-auditlog/pull/172))

### Improvements

- Add Python classifiers for supported Python versions ([#176](https://github.com/jazzband/django-auditlog/pull/176))
- Update README to include steps to release ([#185](https://github.com/jazzband/django-auditlog/pull/185))

### Fixes

- Fix the rendering of the `msg` field with Django 2.0 ([#166](https://github.com/jazzband/django-auditlog/pull/166))
- Mark `LogEntryAdminMixin` methods output as safe where required ([#167](https://github.com/jazzband/django-auditlog/pull/167))


## 0.4.5 (2018-01-12)

### Improvements

Added support for Django 2.0, along with a number of bug fixes.


## 0.4.4 (2017-11-17)

### Improvements

- Use [Tox](https://tox.wiki) to run tests
- Use Codecov to check to coverage before merging
- Django: drop 1.9 support, add 1.11 (LTS) support
- Python: tests against 2.7, 3.4, 3.5 and 3.6 versions
- Add `python-dateutil` to requirements

### Fixes

- Support models with UUID primary keys ([#111](https://github.com/jazzband/django-auditlog/pull/111))
- Add management commands package to setup.py ([#130](https://github.com/jazzband/django-auditlog/pull/130))
- Add `changes_display_dict` property to `LogEntry` model to display diff in a more human readable format ([#94](https://github.com/jazzband/django-auditlog/pull/94))


## 0.4.3 (2017-02-16)

### Fixes

- Fixes cricital bug in admin mixin making the library only usable on Django 1.11


## 0.4.2 (2017-02-16)

_As it turns out, haste is never good. Due to the focus on quickly releasing this version a nasty bug was not spotted, which makes this version only usable with Django 1.11 and above. Upgrading to 0.4.3 is not only encouraged but most likely necessary. Apologies for the inconvenience and lacking quality control._

### Improvements

- Models can be registered with decorators now

### Fixes

- A lot, yes, [_really_ a lot](https://github.com/jjkester/django-auditlog/milestone/8?closed=1), of fixes for the admin integration
- Flush command fixed for Django 1.10


## 0.4.1 (2016-12-27)

### Improvements

- Improved Django Admin pages

### Fixes

- Fixed multithreading issue where the wrong user was written to the log


## 0.4.0 (2016-08-17)

### Breaking changes

- Dropped support for Django 1.7
- Updated dependencies - _please check whether your project works with these higher versions_

### New features

- Management command for deleting all log entries
- Added admin interface (thanks, @crackjack)

### Improvements

- Django: add 1.10 support

### Fixes

- Solved migration error for MySQL users


## 0.3.3 (2016-01-23)

### Fixes

- fix `unregister` method
- `LogEntry.objects.get_for_objects` works properly on PostgreSQL
- Added index in 0.3.2 no longer breaks for users with MySQL databases

### Important notes

- The `object_pk` field is now limited to 255 chars


## 0.3.2 (2015-10-19)

### New functionality

- Django: support 1.9

### Improvements

- Enhanced performance for non-integer primary key lookups


## 0.3.1 (2015-07-29)

### Fixes

- Auditlog data is now correctly stored in the thread.


## 0.3.0 (2015-07-22)

### Breaking changes

- Django: drop out-of-date versions support, support 1.7+
- South is no longer supported

### New functionality

- Workaround for many-to-many support
- Additional data
- Python: support 2.7 and 3.4

### Improvements

- Better diffs
- Remote address is logged through middleware
- Better documentation
- Compatibility with [django-polymorphic](https://pypi.org/project/django-polymorphic/)


## 0.2.1 (2014-07-08)

### New functionality

- South compatibility for `AuditlogHistoryField`


## 0.2.0 (2014-03-08)

Although this release contains mostly bugfixes, the improvements were significant enough to justify a higher version number.

### Improvements

- Signal disconnection fixed
- Model diffs use unicode strings instead of regular strings
- Tests on middleware


## 0.1.1 (2013-12-12)

### New functionality

- Utility methods for using log entry data

### Improvements

- Only save a new log entry if there are actual changes
- Better way of loading the user model in the middleware


## 0.1.0 (2013-10-21)

First beta release of Auditlog.
