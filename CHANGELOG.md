# Changes

## Next Release

#### Breaking Changes

- feat: stop deleting old log entries when a model with the same pk is created (i.e. the pk value is reused) ([#559](https://github.com/jazzband/django-auditlog/pull/559))

#### Improvements

#### Fixes
* fix: only fire the `post_log` signal when the log is created or when there is an error in the process ([#561](https://github.com/jazzband/django-auditlog/pull/561))
* fix: don't set the correlation_id if the `AUDITLOG_CID_GETTER` is `None` ([#565](https://github.com/jazzband/django-auditlog/pull/565))

## 3.0.0-beta.1

#### Breaking Changes

- feat: Change `LogEntry.change` field type to `JSONField` rather than `TextField`. This change include a migration that may take time to run depending on the number of records on your `LogEntry` table ([#407](https://github.com/jazzband/django-auditlog/pull/407))([#495](https://github.com/jazzband/django-auditlog/pull/495))
- Python: Drop support for Python 3.7 ([#546](https://github.com/jazzband/django-auditlog/pull/546))
- feat: Set `AuditlogHistoryField.delete_related` to `False` by default. This is different from the default configuration of Django's `GenericRelation`, but we should not erase the audit log of objects on deletion by default. ([#557](https://github.com/jazzband/django-auditlog/pull/557))

#### Improvements

- Changes the view when it has changes in fields `JSONField`. The `JSONField.encoder` is assigned to `json.dumps`. ([#489](https://github.com/jazzband/django-auditlog/pull/489))
- feat: Added support for Correlation ID. ([#481](https://github.com/jazzband/django-auditlog/pull/481))
- feat: Added pre-log and post-log signals. ([#483](https://github.com/jazzband/django-auditlog/pull/483))
- feat: Make timestamp in LogEntry overwritable. ([#476](https://github.com/jazzband/django-auditlog/pull/476))
- feat: Support excluding field names globally when ```AUDITLOG_INCLUDE_ALL_MODELS``` is enabled. ([#498](https://github.com/jazzband/django-auditlog/pull/498))
- feat: Improved auto model registration to include auto-created models and exclude non-managed models, and automatically register m2m fields for models. ([#550](https://github.com/jazzband/django-auditlog/pull/550))

#### Fixes

- fix: Audit changes to FK fields when saved using `*_id` naming. ([#525](https://github.com/jazzband/django-auditlog/pull/525))
- fix: Fix a bug in audit log admin page when `USE_TZ=False`. ([#511](https://github.com/jazzband/django-auditlog/pull/511))
- fix: Make sure `LogEntry.changes_dict()` returns an empty dict instead of `None` when `json.loads()` returns `None`. ([#472](https://github.com/jazzband/django-auditlog/pull/472))
- fix: Always set remote_addr even if the request has no authenticated user. ([#484](https://github.com/jazzband/django-auditlog/pull/484))
- fix: Fix a bug in getting field's `verbose_name` when model is not accessible. ([508](https://github.com/jazzband/django-auditlog/pull/508))
- fix: Fix a bug in `serialized_data` with F expressions. ([508](https://github.com/jazzband/django-auditlog/pull/508))
- fix: Make log entries read-only in the admin. ([#449](https://github.com/jazzband/django-auditlog/pull/449), [#556](https://github.com/jazzband/django-auditlog/pull/556)) (applied again after being reverted in 2.2.2)

## 2.2.2 (2023-01-16)

#### Fixes
- fix: revert [#449](https://github.com/jazzband/django-auditlog/pull/449) "Make log entries read-only in the admin" as it breaks deletion of any auditlogged model through the admin when `AuditlogHistoryField` is used. ([#496](https://github.com/jazzband/django-auditlog/pull/496))

## 2.2.1 (2022-11-28)

#### Fixes

- fix: Make log entries read-only in the admin. ([#449](https://github.com/jazzband/django-auditlog/pull/449))
- fix: Handle IPv6 addresses in `X-Forwarded-For`. ([#457](https://github.com/jazzband/django-auditlog/pull/457))

## 2.2.0 (2022-10-07)

#### Improvements
- feat: Add `ACCESS` action to `LogEntry` model and allow object access to be logged. ([#436](https://github.com/jazzband/django-auditlog/pull/436))
- feat: Add `serialized_data` field on `LogEntry` model. ([#412](https://github.com/jazzband/django-auditlog/pull/412))
- feat: Display the field name as it would be displayed in Django Admin or use `mapping_field` if available [#428](https://github.com/jazzband/django-auditlog/pull/428)
- feat: New context manager `disable_auditlog` to turn off logging and a new setting `AUDITLOG_DISABLE_ON_RAW_SAVE`
  to disable it during raw-save operations like loaddata. [#446](https://github.com/jazzband/django-auditlog/pull/446)
- Python: Confirm Python 3.11 support ([#447](https://github.com/jazzband/django-auditlog/pull/447))
- feat: Replace the `django.utils.timezone.utc` by `datetime.timezone.utc`. [#448](https://github.com/jazzband/django-auditlog/pull/448)

#### Fixes

- fix: Foreign key values are used to check for changes in related fields instead of object representations. When changes are detected, the foreign key value is persisted in `LogEntry.changes` field instead of object representations. ([#420](https://github.com/jazzband/django-auditlog/pull/420))
- fix: Display `created` timestamp in server timezone ([#404](https://github.com/jazzband/django-auditlog/pull/404))
- fix: Handle port in `remote_addr` ([#417](https://github.com/jazzband/django-auditlog/pull/417))
- fix: Handle the error with AttributeError: 'OneToOneRel' error occur during a `PolymorphicModel` has relation with other models  ([#429](https://github.com/jazzband/django-auditlog/pull/429))
- fix: Support search by custom USERNAME_FIELD ([#432](https://github.com/jazzband/django-auditlog/pull/432))

## 2.1.1 (2022-07-27)

#### Improvements

- feat: Display the diff for deleted objects in the admin ([#396](https://github.com/jazzband/django-auditlog/pull/396))
- Django: Confirm Django 4.1 support ([#406](https://github.com/jazzband/django-auditlog/pull/406))

#### Fixes

- fix: Pin `python-dateutil` to 2.7.0 or higher for compatibility with Python 3.10 ([#401](https://github.com/jazzband/django-auditlog/pull/401))

## 2.1.0 (2022-06-27)

#### Improvements

- feat: Add `--before-date` option to `auditlogflush` to support retention windows ([#365](https://github.com/jazzband/django-auditlog/pull/365))
- feat: Add db_index to the `LogEntry.timestamp` column ([#364](https://github.com/jazzband/django-auditlog/pull/364))
- feat: Add register model from settings ([#368](https://github.com/jazzband/django-auditlog/pull/368))
- Context manager set_actor() for use in Celery tasks ([#262](https://github.com/jazzband/django-auditlog/pull/262))
- Tracking of changes in many-to-many fields ([#309](https://github.com/jazzband/django-auditlog/pull/309))

#### Fixes

- Fix inconsistent changes with JSONField ([#355](https://github.com/jazzband/django-auditlog/pull/355))
- Disable `add` button in admin ui ([#378](https://github.com/jazzband/django-auditlog/pull/378))
- Fix n+1 query problem([#381](https://github.com/jazzband/django-auditlog/pull/381))

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
