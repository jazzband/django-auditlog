# Changes

## 1.0.0 (unreleased)
### Final (unreleased)
### Alpha 1 (1.0a1, 2020-09-07)
## 0.4.8 (2019-11-12)
## 0.4.7 (2019-12-19)
## 0.4.6 (2018-09-18)
## 0.4.5 (2018-01-12)
## 0.4.4 (2017-11-17)
## 0.4.3 (2017-02-16)
## 0.4.2 (2017-02-16)
## 0.4.1 (2016-12-27)
## 0.4.0 (2016-08-17)
## 0.3.3 (2016-01-23)
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
