django-auditlog
===============

[![Build Status](https://travis-ci.org/jjkester/django-auditlog.svg?branch=master)](https://travis-ci.org/jjkester/django-auditlog)
[![Docs](https://readthedocs.org/projects/django-auditlog/badge/?version=latest)](http://django-auditlog.readthedocs.org/en/latest/?badge=latest)

**Please remember that this app is still in development.**
**Test this app before deploying it in production environments.**
**We forked this repo in order to run with python 3.7, as well as make changes which improve our timeline code.**

```django-auditlog``` (Auditlog) is a reusable app for Django that makes logging object changes a breeze. Auditlog tries to use as much as Python and Django’s built in functionality to keep the list of dependencies as short as possible. Also, Auditlog aims to be fast and simple to use.

Auditlog is created out of the need for a simple Django app that logs changes to models along with the user who made the changes (later referred to as actor). Existing solutions seemed to offer a type of version control, which was found excessive and expensive in terms of database storage and performance.

The core idea of Auditlog is similar to the log from Django’s admin. Unlike the log from Django’s admin (```django.contrib.admin```) Auditlog is much more flexible. Also, Auditlog saves a summary of the changes in JSON format, so changes can be tracked easily.

Documentation
-------------

The documentation for the original```django-auditlog``` can be found on http://django-auditlog.readthedocs.org. The source files are available in the ```docs``` folder.

License
-------

Auditlog is licensed under the MIT license (see the ```LICENSE``` file for details).


Darwin 
--------

#### Pull latest code
* Clone repository: `git clone https://github.com/darwin-homes/django-auditlog.git`

#### Homebrew
* Install Homebrew: https://brew.sh/

#### Python
* Install Python 3.7 (with Homebrew on macOS): `brew install python`

#### VirtualEnv
* Create a virtual env: `python3 -m venv venv`
* Activate virtual env: `source venv/bin/activate`

#### Install project dependencies
* Python dependencies: `pip install -r requirements.txt`
* Python dependencies: `pip install -r requirements-test.txt`

#### Setup database
* Install PostgreSQL: (Recommended) Follow steps in https://postgresapp.com/
* May have to use `createdb auditlog_tests_db`
* Seed the database: `invoke reset-env`

#### Migrations
* Do not forget to generate new migrations files after modifying models: `python src/manage.py makemigrations`
* Run migrations: `python src/manage.py migrate`

### Run Tests
* Run tests: `python src/runtests.py`